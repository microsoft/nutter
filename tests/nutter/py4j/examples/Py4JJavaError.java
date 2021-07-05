package py4j.examples;

import py4j.GatewayServer;
import java.lang.Exception;

public class Py4JJavaError {
    public static void main(String[] args) {
        GatewayServer gatewayServer = new GatewayServer(new Py4JJavaError());
        gatewayServer.start();
    }
}
