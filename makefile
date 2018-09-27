OBJS=shell.o ssh_conn.o argument_parser.o cJSON.o cartesian.o json_readers.o

all: $(OBJS)
	gcc $(OBJS) -o client -lssh

shell.o: shell.c cartesian.o
	gcc -c shell.c 

ssh_conn.o: ssh_conn/ssh_conn.c
	gcc -c ssh_conn/ssh_conn.c

argument_parser.o: argument_parser.c shell.o
	gcc -c argument_parser.c

cJSON.o: cJSON/cJSON.c
	gcc -c cJSON/cJSON.c

cartesian.o: parsers/cartesian.c 
	gcc -c parsers/cartesian.c

json_readers.o: cJSON.o parsers/json_readers.c
	gcc -c parsers/json_readers.c

test: cJSON.o test_json.c 
	gcc cJSON.o test_json.c -o json 

	