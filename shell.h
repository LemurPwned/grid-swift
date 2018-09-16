#include "cJSON.h"

#define MAX_CONF_TEXT_LEN 100
#define MAX_PARAMETER_NUMBER 5

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

int queue_script_writer(struct oommf_config *conf_spec);
int oommf_task_executor(char *config_file);
int parse_parameter_list(const cJSON *parameter_list, PM_LIST pm_list[], int *param_length);
int oommf_config_reader(const char *config_file, OOMMF_CONFIG *o_conf);
int compose_parameter_combinations(PM_LIST *pm, int parameter_number);
char *readFile(char *fileName);