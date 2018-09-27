#include "cJSON.h"

#define MAX_CONF_TEXT_LEN 100
#define MAX_PARAMETER_NUMBER 5
#define DELIMITER "/"

typedef struct parameter_sweep
{
    char param_name[MAX_CONF_TEXT_LEN];
    double start;
    double stop;
    double step;
} PM_LIST;

typedef struct oommf_config
{
    char name[MAX_CONF_TEXT_LEN];
    char input_script[MAX_CONF_TEXT_LEN];
    char remote_output_dir[MAX_CONF_TEXT_LEN];
    char grant[MAX_CONF_TEXT_LEN];
    char walltime[MAX_CONF_TEXT_LEN];
    char tcl_path[MAX_CONF_TEXT_LEN];
    int core_count;
    int nodes;
    int threads;
    char **modules;
    int modules_number;
    int parameter_number;
    PM_LIST pm[MAX_PARAMETER_NUMBER];
} OOMMF_CONFIG;

int queue_script_writer(OOMMF_CONFIG *conf_spec, char filepath[], char parameter_string[]);
int oommf_task_executor(char *config_file);
int parse_parameter_list(const cJSON *parameter_list, PM_LIST pm_list[], int *param_length);
int oommf_config_reader(const char *config_file, OOMMF_CONFIG *o_conf);
int compose_parameter_combinations(PM_LIST pm[], int parameter_number,
                                   char **param_list_string, char ***pm_string_list,
                                   int pm_step_nums[]);
char *readFile(char *fileName);
void remove_spaces(const char *input, char *result);
void create_dir(char directory_path[]);