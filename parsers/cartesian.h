
#if !defined(CARTESIAN)
#define CARTESIAN

void cartesian(char **set, char **resultSet, int setLen, int resLen);
int compose_parameter_combinations(int parameter_number,
                                   char **param_list_string, char ***pm_string_list,
                                   int pm_step_nums[]);
#endif // CARTESIAN
