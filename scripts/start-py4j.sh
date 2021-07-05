#!/bin/bash

# Script requirements:
# - Py4J installed
# - Java JDK available, in PATH
# The script does not return an error code if the environment is not ready,
# only a warning message.

if ! python -c 'import py4j' 2>/dev/null
then
    echo "Warning: Py4j not installed, Py4J gateway not started"
    exit 0
fi

if ! command -v javac >/dev/null
then
    echo "Warning: Java not found, Py4J gateway not started"
    exit 0
fi

# Path to py4ja.b.c.d.jar

exec_prefix=$(python -c 'import sys; print(sys.exec_prefix)')
py4j_jar=$(echo ${exec_prefix}/share/py4j/py4j*.jar)

export CLASSPATH=.:${py4j_jar}

# Compile and run Py4J gateway

cd tests/nutter

# Compile
javac py4j/examples/Py4JJavaError.java

# Run in background
java py4j.examples.Py4JJavaError &
