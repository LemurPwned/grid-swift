#if !defined(CONFIG_DEF)
#define CONFIG_DEF

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

#endif // CONFIG_DEF
