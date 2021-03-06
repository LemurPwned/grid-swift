#if !defined(CONFIG_DEF)
#define CONFIG_DEF

#define MAX_CONF_TEXT_LEN 500
#define MAX_PARAMETER_NUMBER 5
#define MAX_PLAIN_LIST_LENGTH 40
#define DELIMITER "/"

typedef struct user_info
{
    char username[MAX_CONF_TEXT_LEN];
    char hostname[MAX_CONF_TEXT_LEN];
} USER_DATA;
typedef struct parameter_sweep
{
    char param_name[MAX_CONF_TEXT_LEN];
    double start;
    double stop;
    double step;
    int plain;
    double plain_list[MAX_PLAIN_LIST_LENGTH];
} PM_LIST;

typedef struct oommf_config
{
    char name[MAX_CONF_TEXT_LEN];
    char local_script_import_location[MAX_CONF_TEXT_LEN];
    char remote_script_location[MAX_CONF_TEXT_LEN];
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
