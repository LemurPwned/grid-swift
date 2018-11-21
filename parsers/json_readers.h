
#if !defined(JSON_PARSERS)
#define JSON_PARSERS

#include "../cJSON/cJSON.h"
#include "../structure_defs/config_def.h"

int parse_module_list(const cJSON *module_list, OOMMF_CONFIG *oommf_config);
char *readFile(char *fileName);
int parse_parameter_list(const cJSON *parameter_list, PM_LIST pm_list[], int *param_length);
int oommf_config_reader(const char *config_file, OOMMF_CONFIG *o_conf);
void extract_basename(char *filepath, char *basename);
void replace_space(const char *input, char *result);
void remove_spaces(const char *input, char *result);

#endif // JSON_PARSERS
