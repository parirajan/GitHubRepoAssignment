public interface JmsClient {
    void sendMessage(String message) throws Exception;
    String receiveMessage() throws Exception;
    void close() throws Exception;
}
