OBJS=shell.o argument_parser.o cJSON.o cartesian.o json_readers.o
T_OBJS=file_asserts.o utils.o
CC=gcc -std=c99 -pedantic

all: $(OBJS)
	$(CC) $(OBJS) -o client 

shell.o: shell.c cartesian.o utils.o
	$(CC) -c shell.c 

argument_parser.o: argument_parser.c shell.o
	$(CC) -c argument_parser.c

cJSON.o: cJSON/cJSON.c
	$(CC) -c cJSON/cJSON.c

cartesian.o: parsers/cartesian.c 
	$(CC) -c parsers/cartesian.c

json_readers.o: cJSON.o parsers/json_readers.c
	$(CC) -c parsers/json_readers.c

# test: cJSON.o test_json.c 
# 	$(CC) cJSON.o test_json.c -o json 

utils.o: utils/utils.c 
	$(CC) -c utils/utils.c
	
file_asserts.o: asserts/file_asserts.c
	$(CC) -c asserts/file_asserts.c 

tests: $(T_OBJS) 
	$(CC) $(T_OBJS) -o asserts_test