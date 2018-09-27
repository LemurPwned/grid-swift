#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>

#include "shell.h"

#define STR_CONF_ELEMENTS 6
#define NUM_CONF_ELEMENTS 3

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
        int number_of_steps = (int)(diff / pm[i].step);
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
            // printf("PARAM: %s\n", pm_string_list[i][j]);
        }
        pm_step_nums[i] = number_of_steps;
        // avoid consequent multiplicatiion by zero
        total_combinations = (total_combinations == 0) ? number_of_steps : total_combinations * number_of_steps;
    }
    return total_combinations;
}

int oommf_task_executor(char *config_file)
{
    // define config struct
    const char *filename = readFile(config_file);
    OOMMF_CONFIG *omf_conf = malloc(sizeof(struct oommf_config));
    oommf_config_reader(filename, omf_conf);
    printf("%s, %s, %d, %s\n", omf_conf->name, omf_conf->remote_output_dir, omf_conf->core_count,
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
    system("rm -rf sim-dir");
    create_dir(omf_conf->remote_output_dir);

    char filepath[MAX_CONF_TEXT_LEN],
        indir[MAX_CONF_TEXT_LEN],
        final_parameter_name[MAX_CONF_TEXT_LEN];

    for (int i = 0; i < combinations; i++)
    {
        // create sub directory
        strcpy(filepath, omf_conf->remote_output_dir);
        strcat(filepath, DELIMITER);
        // remove spaces for readibility
        remove_spaces(param_list_string[i], indir);
        strcat(filepath, indir);
        create_dir(filepath);
        // create file
        strcat(filepath, DELIMITER);
        strcat(filepath, "script.pbs");
        // write a file for simulation
        sprintf(final_parameter_name, "\"%s\"", param_list_string[i]);
        queue_script_writer(omf_conf, filepath, final_parameter_name);
        // TODO: here run script in the background using the filepath
        // clear all paths
        bzero(final_parameter_name, sizeof(final_parameter_name));
        bzero(filepath, sizeof(filepath));
        bzero(indir, sizeof(indir));
    }
    return 0;
}

int queue_script_writer(OOMMF_CONFIG *conf_spec, char filepath[], char parameter_string[])
{
    FILE *output;
    output = fopen(filepath, "w");
    if (output == NULL)
    {
        perror("File error");
        return -1;
    }

    fprintf(output, "#SBATCH -J %s\n", conf_spec->name);
    fprintf(output, "#SBATCH - N %d\n", conf_spec->nodes);
    fprintf(output, "#SBATCH --ntasks-per-node=%d\n", conf_spec->core_count);
    fprintf(output, "#SBATCH -A %s\n", conf_spec->grant);
    fprintf(output, "#SBATCH -p plgrid\n");
    fprintf(output, "#SBATCH --output=\"%s\"\n", conf_spec->remote_output_dir);
    fprintf(output, "#SBATCH --error=\"%s\"\n", conf_spec->remote_output_dir);
    fprintf(output, "date\n");
    for (int i = 0; i < conf_spec->modules_number; i++)
    {
        fprintf(output, "module load %s\n", conf_spec->modules[i]);
    }
    fprintf(output, "export MKL_HOME=\n");
    fprintf(output, "tclsh %s boxsi %s -threads %d -parameters %s\n", conf_spec->tcl_path,
            conf_spec->input_script,
            conf_spec->threads,
            parameter_string);
    fprintf(output, "date\n");
    // close the file
    fclose(output);
    return 0;
}

void create_dir(char directory_path[])
{
    struct stat sb = {0};
    if (stat(directory_path, &sb) == 0)
    {
        mkdir(directory_path, 0777);
        printf("Directory %s does exist\n", directory_path);
        // exit(-1);
        // rmdir(directory_path);
    }
    else
    {
        // printf("Creating directory %s...\n", directory_path);
        if (mkdir(directory_path, 0777) && errno != EEXIST)
            printf("error while trying to create '%s'\n%m\n", directory_path);
    }
}