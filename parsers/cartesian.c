void cartesian(char **set, char **resultSet, int setLen, int resLen)
{
    if ((setLen == 0))
    {
        perror("Only res set can be empty\n");
        exit(-1);
    }
    else if (resLen == 0)
    {
        printf("resLen is 0\n");
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
                printf("%s --- %s\n", set[j], resultSetCopy[i]);
                sprintf(resultSet[i * setLen + j], "%s, %s", set[j], resultSetCopy[i]);
            }
        }
        free(resultSetCopy);
    }
}
int main(void)
{
    int setA[4] = {1, 2, 3, 4};
    int setB[3] = {5, 6, 7};
    int setC[2] = {8, 9};
    int setLen[3] = {4, 3, 2};
    int tsetLen = 4 * 3 * 2;
    // int *sets[3] = {setA, setB, setC};

    char *sA[4] = {"1", "2", "3", "4"};
    char *sB[3] = {"5", "6", "7"};
    char *sC[2] = {"8", "9"};

    char **sets[3] = {sA, sB, sC};
    char **C;
    C = malloc(tsetLen * sizeof(char *));
    for (int i = 0; i < tsetLen; i++)
    {
        C[i] = malloc(20 * sizeof(char));
    }
    int resSize = 0;
    for (int i = 0; i < 3; i++)
    {
        // A is bigger
        cartesian(sets[i], C, setLen[i], resSize);
        resSize = (resSize == 0) ? setLen[i] : resSize * setLen[i];
        printf("SET LENGTH %d\n", resSize);
        for (int i = 0; i < resSize; i++)
        {
            printf("%s\n", C[i]);
        }
        printf("END OF ITERATION\n");
    }
}