#include "cartesian.h"

void cartesian(char **set, char **resultSet, int setLen, int resLen)
{
    if ((setLen == 0))
    {
        perror("Only res set can be empty\n");
        exit(-1);
    }
    else if (resLen == 0)
    {
        perror("resLen is 0\n");
        for (int i = 0; i < setLen; i++)
        {
            sprintf(resultSet[i], "%s", set[i]);
        }
    }
    else
    {
        // copy the resultArray to avoid modyfying while filling it
        char **resultSetCopy = malloc(resLen * sizeof(char *));
        for (int i = 0; i < resLen; i++)
        {
            resultSetCopy[i] = malloc(20 * sizeof(char));
            strcpy(resultSetCopy[i], resultSet[i]);
        }
        for (int i = 0; i < resLen; i++)
        {
            for (int j = 0; j < setLen; j++)
            {
                // printf("%s --- %s\n", set[j], resultSetCopy[i]);
                sprintf(resultSet[i * setLen + j], "%s %s", set[j], resultSetCopy[i]);
            }
        }
        free(resultSetCopy);
    }
}

int compose_parameter_combinations(int parameter_number,
                                   char **param_list_string, char ***pm_string_list,
                                   int pm_step_nums[])
{
    /* 
    combine set 1 with set 2 as set 12, then combine set 12 with set 3 as set123 etc.
    in general: set 1...N combination set N+1 gives all set combinations for N+1 sets.
    */

    // now combinations
    int param_list_string_size = 0;
    for (int i = 0; i < parameter_number; i++)
    {
        cartesian(pm_string_list[i], param_list_string, pm_step_nums[i], param_list_string_size);
        param_list_string_size = (param_list_string_size == 0) ? pm_step_nums[i] : param_list_string_size * pm_step_nums[i];
    }
    return 0;
}