
#define MAX_CONF_TEXT_LEN 100
#define MAX_PARAMETER_NUMBER 5


typedef struct parameter_sweep{
    char param_name[MAX_CONF_TEXT_LEN];
    char start[MAX_CONF_TEXT_LEN];
    char stop[MAX_CONF_TEXT_LEN];
    char step[MAX_CONF_TEXT_LEN];
} PM_LIST;

typedef struct oommf_config{
    char name[MAX_CONF_TEXT_LEN];
    char input_script[MAX_CONF_TEXT_LEN];
    char remote_output_dir[MAX_CONF_TEXT_LEN];
    char grant[MAX_CONF_TEXT_LEN];
    char walltime[MAX_CONF_TEXT_LEN];
    char tcl_path[MAX_CONF_TEXT_LEN];
    int core_count;
    int nodes;  
    PM_LIST pm[MAX_PARAMETER_NUMBER];
} OOMMF_CONFIG;



int queue_script_writer(struct oommf_config *conf_spec);