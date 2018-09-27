OBJS=shell.o argument_parser.o cJSON.o cartesian.o json_readers.o
CC=gcc -std=c99 -pedantic

all: $(OBJS)
	$(CC) $(OBJS) -o client 

shell.o: shell.c cartesian.o
	$(CC) -c shell.c 

argument_parser.o: argument_parser.c shell.o
	$(CC) -c argument_parser.c

cJSON.o: cJSON/cJSON.c
	$(CC) -c cJSON/cJSON.c

cartesian.o: parsers/cartesian.c 
	$(CC) -c parsers/cartesian.c

json_readers.o: cJSON.o parsers/json_readers.c
	$(CC) -c parsers/json_readers.c

test: cJSON.o test_json.c 
	$(CC) cJSON.o test_json.c -o json 

	
