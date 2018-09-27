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
