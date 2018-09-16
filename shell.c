#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "shell.h"
#include "ssh_conn.h"

#define STR_CONF_ELEMENTS 6
#define NUM_CONF_ELEMENTS 3

int oommf_task_executor(char *config_file)
{
    // define config struct
    const char *filename = readFile(config_file);
    OOMMF_CONFIG *omf_conf = malloc(sizeof(struct oommf_config));
    oommf_config_reader(filename, omf_conf);
    printf("%s, %s, %d, %s\n", omf_conf->name, omf_conf->remote_output_dir, omf_conf->core_count,
           omf_conf->walltime);

    // for every set of parameters make a string and create as separate simulation file
    // queue_script_writer(omf_conf);
    // scp_file("testfile.pbs", omf_conf.username, omf_conf.server, omf_conf.remote_output_dir);

    // upload the file to the queue system along with the scripts
    return 0;
}

int parse_parameter_list(const cJSON *parameter_list, PM_LIST pm_list[], int *param_length)
{
    int iterator = 0;
    while (parameter_list)
    {
        cJSON *name = cJSON_GetObjectItemCaseSensitive(parameter_list, "name");
        if (name != NULL)
        {
            strcpy(pm_list[iterator].param_name, name->valuestring);
        }
        else
        {
            perror("{\"name\"} parameter not found in conf.json/parameter_list");
        }
        cJSON *start = cJSON_GetObjectItemCaseSensitive(parameter_list, "start");
        if (start != NULL)
        {
            strcpy(pm_list[iterator].start, start->valuestring);
        }
        else
        {
            perror("{\"start\"} parameter not found in conf.json/parameter_list");
        }
        cJSON *stop = cJSON_GetObjectItemCaseSensitive(parameter_list, "stop");
        if (stop != NULL)
        {
            strcpy(pm_list[iterator].stop, stop->valuestring);
        }
        else
        {
            perror("{\"stop\"} parameter not found in conf.json/parameter_list");
        }
        cJSON *step = cJSON_GetObjectItemCaseSensitive(parameter_list, "step");
        if (step != NULL)
        {
            strcpy(pm_list[iterator].step, step->valuestring);
        }
        else
        {
            perror("{\"step\"} parameter not found in conf.json/parameter_list");
        }
        parameter_list = parameter_list->next;
        iterator++;
    }
    *param_length = iterator;
    return 0;
}

int parse_module_list(const cJSON *module_list, OOMMF_CONFIG *oommf_config)
{
    int iterator = 0;
    cJSON *arrayItem;
    oommf_config->modules_number = cJSON_GetArraySize(module_list);
    // malloc for the whole modules char * array
    oommf_config->modules = malloc(oommf_config->modules_number * sizeof(char *));
    for (int i = 0; i < oommf_config->modules_number; i++)
    {
        arrayItem = cJSON_GetArrayItem(module_list, i);
        // malloc for each element of the array
        oommf_config->modules[i] = malloc(strlen(arrayItem->valuestring + 1) * sizeof(char));
        strcpy(oommf_config->modules[i], arrayItem->valuestring);
    }
    return 0;
}

int queue_script_writer(OOMMF_CONFIG *conf_spec)
{
    FILE *output;
    output = fopen("testfile.pbs", "w");
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
            "placeholder");
    fprintf(output, "date\n");

    // close the file
    fclose(output);
    return 0;
}

int oommf_config_reader(const char *config_file, OOMMF_CONFIG *o_conf)
{
    const cJSON *name, *params, *modules, *num = NULL;
    int status = 0;
    cJSON *config_json = cJSON_Parse(config_file);
    if (config_json == NULL)
    {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr != NULL)
        {
            fprintf(stderr, "Error before: %s\n", error_ptr);
        }
        status = 0;
    }

    name = cJSON_GetObjectItemCaseSensitive(config_json, "name");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->name, name->valuestring);
    }
    else
        perror("{\"name\"} parameter not found in conf.json");
    name = cJSON_GetObjectItemCaseSensitive(config_json, "input_script");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->input_script, name->valuestring);
    }
    else
        perror("{\"input_script\"} parameter not found in conf.json");

    name = cJSON_GetObjectItemCaseSensitive(config_json, "remote_output_dir");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->remote_output_dir, name->valuestring);
    }
    else
        perror("{\"remote_output_dir\"} parameter not found in conf.json");
    name = cJSON_GetObjectItemCaseSensitive(config_json, "grant");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->grant, name->valuestring);
    }
    else
    {
        perror("{\"grant\"} parameter not found in conf.json");
    }
    name = cJSON_GetObjectItemCaseSensitive(config_json, "walltime");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->walltime, name->valuestring);
    }
    else
        perror("{\"walltime\"} parameter not found in conf.json");

    num = cJSON_GetObjectItemCaseSensitive(config_json, "core_count");
    if (cJSON_IsNumber(num))
    {
        o_conf->core_count = num->valueint;
    }
    else
        perror("{\"core_count\"} parameter not found in conf.json");

    num = cJSON_GetObjectItemCaseSensitive(config_json, "nodes");
    if (cJSON_IsNumber(num))
    {
        o_conf->nodes = num->valueint;
    }
    else
        perror("{\"nodes\"} parameter not found in conf.json");

    num = cJSON_GetObjectItemCaseSensitive(config_json, "threads");
    if (cJSON_IsNumber(num))
    {
        o_conf->threads = num->valueint;
    }
    else
        perror("{\"threads\"} parameter not found in conf.json");

    name = cJSON_GetObjectItemCaseSensitive(config_json, "tcl_path");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->tcl_path, name->valuestring);
    }
    else
        perror("{\"tcl_path\"} parameter not found in conf.json");

    params = cJSON_GetObjectItemCaseSensitive(config_json, "parameter_list");
    if (cJSON_IsArray(params) && params->child != NULL)
    {
        int param_length;
        parse_parameter_list(params->child, o_conf->pm, &param_length);
        o_conf->parameter_number = param_length;
        for (int i = 0; i < param_length; i++)
        {
            printf("%s: %s to %s by %s\n", o_conf->pm[i].param_name,
                   o_conf->pm[i].start, o_conf->pm[i].stop, o_conf->pm[i].step);
        }
    }
    else
        perror("{\"parameter_list\"} parameter not found in conf.json");

    modules = cJSON_GetObjectItemCaseSensitive(config_json, "modules");
    if (cJSON_IsArray(modules) && modules->child != NULL)
    {
        parse_module_list(modules, o_conf);
        for (int i = 0; i < o_conf->modules_number; i++)
        {
            printf("module: %s\n", o_conf->modules[i]);
        }
    }
    else
        perror("modules list is not an array");
    cJSON_Delete(config_json);
    // printf("All parameters parsed successfully");
    return 0;
}

char *readFile(char *fileName)
{
    FILE *file = fopen(fileName, "r");
    char *filetext;
    size_t n = 0;
    int c;

    if (file == NULL)
        return NULL; //could not open file
    filetext = malloc(1000);
    while ((c = fgetc(file)) != EOF)
    {
        filetext[n++] = (char)c;
    }
    // terminate on null character
    filetext[n] = '\0';

    return filetext;
}
