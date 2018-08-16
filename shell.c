#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "shell.h"
#include "ssh_conn.h"

int oommf_task_executor(char *config_file){
    // define config struct
    const char *filename = readFile(config_file);
    OOMMF_CONFIG omf_conf;
    oommf_config_reader(filename, &omf_conf);
    printf("%s, %s, %d, %s\n", omf_conf.name, omf_conf.remote_output_dir, omf_conf.core_count, 
                            omf_conf.walltime); 
    queue_script_writer(&omf_conf);
    scp_file("testfile.pbs", omf_conf.username, omf_conf.server, omf_conf.remote_output_dir);
    
    // upload the file to the queue system along with the scripts
    return 0;
}

int parse_parameter_list(const cJSON *parameter_list, PM_LIST pm_list[], intle *param_length){
    int iterator = 0;
    while (parameter_list){
        cJSON *name = cJSON_GetObjectItem(parameter_list, "name");
        if (name != NULL){
            strcpy(pm_list[iterator].param_name, name->valuestring);
        }
        cJSON *start = cJSON_GetObjectItem(parameter_list, "start");
        if (start != NULL){
            strcpy(pm_list[iterator].start, start->valuestring);
        }
        cJSON *stop = cJSON_GetObjectItem(parameter_list, "stop");
        if (stop != NULL){
            strcpy(pm_list[iterator].stop, stop->valuestring);
        }
        cJSON *step = cJSON_GetObjectItem(parameter_list, "step");
        if (step != NULL){
            strcpy(pm_list[iterator].step, step->valuestring);
        }
        parameter_list=parameter_list->next;
        iterator++;
    }
    *param_length = iterator;
    return 0;
}

int queue_script_writer(OOMMF_CONFIG *conf_spec){
    FILE *output;
    output = fopen("testfile.pbs", "w");
    if (output == NULL){
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
    
    // close file
    fclose(output);
    return 0;
}

int oommf_config_reader(const char *config_file, OOMMF_CONFIG *o_conf){
    const cJSON *name, *params = NULL;
    
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
    name = cJSON_GetObjectItemCaseSensitive(config_json, "input_script");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->input_script, name->valuestring);
    }    
    name = cJSON_GetObjectItemCaseSensitive(config_json, "remote_output_dir");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->remote_output_dir, name->valuestring);
    }    
    name = cJSON_GetObjectItemCaseSensitive(config_json, "grant");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->grant, name->valuestring);
    }    
    name = cJSON_GetObjectItemCaseSensitive(config_json, "walltime");
    if (cJSON_IsString(name) && (name->valuestring != NULL))
    {
        strcpy(o_conf->walltime, name->valuestring);
    }
    name = cJSON_GetObjectItemCaseSensitive(config_json, "core_count");
    if (cJSON_IsNumber(name))
    {
        o_conf->core_count = name->valueint;
    }
    name = cJSON_GetObjectItemCaseSensitive(config_json, "nodes");
    if (cJSON_IsNumber(name))
    {
        o_conf->nodes = name->valueint;
    }
    params = cJSON_GetObjectItemCaseSensitive(config_json, "parameter_list");
    if (cJSON_IsArray(params) && params->child != NULL)
    {   
        int param_length;
        parse_parameter_list(params->child, o_conf->pm, &param_length);
        for (int i = 0; i < param_length; i++){
            printf("%s: %s to %s by %s\n", o_conf->pm[i].param_name, 
                    o_conf->pm[i].start, o_conf->pm[i].stop, o_conf->pm[i].step);
        }
    }
    else perror("parameter list is not an array");
    cJSON_Delete(config_json);
    return status;
}

char *readFile(char *fileName){
    FILE *file = fopen(fileName, "r");
    char *filetext;
    size_t n = 0;
    int c;

    if (file == NULL)
        return NULL; //could not open file
    filetext = malloc(1000);
    while ((c = fgetc(file)) != EOF)    {
        filetext[n++] = (char) c;
    }
    // terminate on null character
    filetext[n] = '\0';        

    return filetext;
}

