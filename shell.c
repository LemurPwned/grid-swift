#include "shell.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdarg.h>
#include <errno.h>

int fill_numerical_parameter_arrays(double **pm_numerical_list,
                                    char ***pm_string_list,
                                    int pm_step_nums[],
                                    PM_LIST pm[], int parameter_number)
{
    // fill the lists with parameters (unravel the structure)
    // total possible combinations is a simple cartesian products
    int total_combinations = 0;
    for (int i = 0; i < parameter_number; i++)
    {
        printf("PARAMETER SWEEP %s\n", pm[i].param_name);
        printf("start: %f, stop: %f\n", pm[i].start, pm[i].stop,
               pm[i].start, pm[i].stop);
        double diff = pm[i].stop - pm[i].start;
        int number_of_steps = (int)(diff / pm[i].step) + 1;
        double mod = diff - (double)(number_of_steps)*pm[i].step;
        double list_len = mod == 0.0
                              ? diff + 1
                              : diff / pm[i].step;
        printf("Deduced list length %d\n", number_of_steps);
        pm_numerical_list[i] = malloc(number_of_steps * sizeof(double));
        pm_string_list[i] = malloc(number_of_steps * sizeof(char *));
        for (int j = 0; j < number_of_steps; j++)
        {
            pm_numerical_list[i][j] = pm[i].start + (float)j * pm[i].step;
            // printf("%g\n", pm_numerical_list[i][j]);
            pm_string_list[i][j] = malloc(MAX_CONF_TEXT_LEN * sizeof(char));
            sprintf(pm_string_list[i][j], "%s %g", pm[i].param_name, pm_numerical_list[i][j]);
            printf("PARAM: %s\n", pm_string_list[i][j]);
        }
        pm_step_nums[i] = number_of_steps;
        // avoid consequent multiplicatiion by zero
        total_combinations = (total_combinations == 0) ? number_of_steps : total_combinations * number_of_steps;
    }
    return total_combinations;
}

int oommf_task_executor(char *config_file, USER_DATA *ud)
{
    // define config struct
    const char *filename = readFile(config_file);
    OOMMF_CONFIG *omf_conf = malloc(sizeof(struct oommf_config));
    oommf_config_reader(filename, omf_conf);
    printf("%s, %s, %s, %d, %s\n", omf_conf->name, omf_conf->local_script_import_location, omf_conf->remote_script_location, omf_conf->core_count,
           omf_conf->walltime);
    // for every set of parameters make a string and create as separate simulation file
    double **pm_numerical_list;
    char ***pm_string_list;
    char **param_list_string;
    // this holds unraveled parameters from start to stop by step
    pm_numerical_list = malloc(omf_conf->parameter_number * sizeof(double *));
    // this holds unraveled parameters from start to stop by step in string format
    pm_string_list = malloc(omf_conf->parameter_number * sizeof(char **));
    // this holds the lengths of each unraveled parameter list
    int pm_step_nums[omf_conf->parameter_number];
    int combinations = fill_numerical_parameter_arrays(pm_numerical_list,
                                                       pm_string_list,
                                                       pm_step_nums,
                                                       omf_conf->pm,
                                                       omf_conf->parameter_number);
    if (combinations <= 0)
    {
        fprintf(stderr, "Invalid number of combinations! %d", combinations);
        exit(-1);
    }
    // this holds unraveled parameters combinations
    param_list_string = malloc(combinations * sizeof(char *));
    for (int i = 0; i < combinations; i++)
    {
        param_list_string[i] = malloc(MAX_CONF_TEXT_LEN * sizeof(char));
    }
    compose_parameter_combinations(omf_conf->parameter_number,
                                   param_list_string,
                                   pm_string_list,
                                   pm_step_nums);
    // check if directory exists

    char project_name[MAX_CONF_TEXT_LEN];
    sprintf(project_name, "%s/%s", omf_conf->local_script_import_location, omf_conf->name);

    // now import file from remote
    printf("Copying file from remote ... \n");
    create_dir(project_name, 0);
    char command[MAX_CONF_TEXT_LEN];
    sprintf(command, "cp %s %s", omf_conf->remote_script_location, project_name);
    system(command);

    char filepath[MAX_CONF_TEXT_LEN],
        indir[MAX_CONF_TEXT_LEN],
        final_parameter_name[MAX_CONF_TEXT_LEN],
        mif_basename[MAX_CONF_TEXT_LEN], // relative path to mif
        mif_path[MAX_CONF_TEXT_LEN];

    extract_basename(omf_conf->remote_script_location, mif_basename);

    for (int i = 0; i < combinations; i++)
    {
        // remove spaces for readibility
        replace_space(param_list_string[i], indir);
        // create path to the directory of a single combination
        sprintf(filepath, "%s%s%s", project_name, DELIMITER, indir);
        // create a directory for a parameter combination
        create_dir(filepath, 1);

        // create a new path to the mif
        sprintf(mif_path, "%s%s%s", filepath, DELIMITER, mif_basename);
        // copy mif from previous path to the current one
        bzero(command, sizeof(command));
        sprintf(command, "cp %s %s", omf_conf->remote_script_location, mif_path);
        system(command);
        // prepare the filepath for the script
        strcat(filepath, DELIMITER);
        strcat(filepath, "script.pbs");
        // write a file for simulation
        sprintf(final_parameter_name, "\"%s\"", param_list_string[i]);
        queue_script_writer(omf_conf, filepath, final_parameter_name, mif_path);

        bzero(command, sizeof(command));
        sprintf(command, "sbatch %s\n", filepath);
        system(command);
        // clear all paths
        bzero(final_parameter_name, sizeof(final_parameter_name));
        bzero(filepath, sizeof(filepath));
        bzero(indir, sizeof(indir));
    }
    return 0;
}

int queue_script_writer(OOMMF_CONFIG *conf_spec, char filepath[], char parameter_string[], char mif_path[])
{
    FILE *output;
    output = fopen(filepath, "w");
    if (output == NULL)
    {
        perror("File error");
        return -1;
    }
    fprintf(output, "#!/bin/bash\n");
    fprintf(output, "#SBATCH -J %s_(%s)\n", conf_spec->name, parameter_string);
    fprintf(output, "#SBATCH -N %d\n", conf_spec->nodes);
    fprintf(output, "#SBATCH --ntasks-per-node=%d\n", conf_spec->core_count);
    fprintf(output, "#SBATCH --time=%s\n", conf_spec->walltime);
    fprintf(output, "#SBATCH -A %s\n", conf_spec->grant);
    fprintf(output, "#SBATCH -p plgrid\n");
    fprintf(output, "#SBATCH --output=\"%s_output.txt\"\n", filepath);
    fprintf(output, "#SBATCH --error=\"%s_error.txt\"\n", filepath);
    fprintf(output, "date\n");
    for (int i = 0; i < conf_spec->modules_number; i++)
    {
        fprintf(output, "module load %s\n", conf_spec->modules[i]);
    }
    fprintf(output, "export MKL_HOME=\n");
    fprintf(output, "tclsh %s boxsi %s -threads %d -parameters %s\n",
            conf_spec->tcl_path,
            mif_path,
            conf_spec->threads,
            parameter_string);
    fprintf(output, "date\n");
    // close the file
    fclose(output);
    return 0;
}

void create_dir(char directory_path[], int force_removal)
{
    struct stat sb = {0};
    if ((stat(directory_path, &sb) == 0) && S_ISDIR(sb.st_mode))
    {
        if (force_removal == 1)
        {
            char command[MAX_CONF_TEXT_LEN];
            sprintf(command, "rm -rf %s", directory_path);
            system(command);
            create_dir(directory_path, 0);
        }
        else
        {
            // if removal is not forced, ask the user
            printf("Directory %s does exist. Do you want to remove it? [Y/n]\n", directory_path);
            char response[200];
            fscanf(stdin, "%s", response);
            if ((!strcmp(response, "Yes")) || (!strcmp(response, "Y")) ||
                (!strcmp(response, "y")) || (!strcmp(response, "yes")))
            {
                printf("Removing the directory and proceeding...\n");
                rmdir(directory_path);
            }
            else
            {
                printf("Leaving, the directory was not removed...\n");
                exit(0);
            }
        }
    }
    else
    {
        if (mkdir(directory_path, 0777) && errno != EEXIST)
            printf("error while trying to create '%s'\n%m\n", directory_path);
    }
}
