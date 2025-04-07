public void performWriteWithReadBeforeWrite(AerospikeClient client, WritePolicy writePolicy, Key key, Bin bin) {
    try {
        // Attempt to write the record
        client.put(writePolicy, key, bin);
    } catch (AerospikeException e) {
        // Check if the exception indicates an in-doubt response
        if (e.getInDoubt()) {
            System.out.println("Write operation returned in-doubt. Verifying record existence via read...");
            boolean recordExists = false;
            int retryCount = 3;
            
            // Retry reading the record a few times to verify if the write eventually succeeded
            while (retryCount-- > 0) {
                Record record = client.get(null, key);
                if (record != null) {
                    System.out.println("Record found on disk. Treating write as successful.");
                    recordExists = true;
                    break;
                }
                // Wait briefly before trying again (backoff period)
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
            
            if (!recordExists) {
                // If the record still isn't found, decide on a course of action.
                // Depending on your business logic, you could retry the write operation or handle it as a failure.
                System.out.println("Record not found after retries. Retrying write operation...");
                client.put(writePolicy, key, bin);
            }
        } else {
            // If the exception is not related to an in-doubt scenario, rethrow or handle it as needed.
            throw e;
        }
    }
}
