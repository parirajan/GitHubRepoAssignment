#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>

int main() {
    // Load the Python shared library
    void *handle = dlopen("libpython3.so", RTLD_LAZY);
    if (!handle) {
        fprintf(stderr, "Failed to load libpython3.so: %s\n", dlerror());
        return 1;
    }

    // Define function pointers for the Python API functions
    void (*Py_Initialize)(void);
    const char* (*Py_GetVersion)(void);
    void (*Py_Finalize)(void);

    // Resolve symbols for the required functions
    Py_Initialize = dlsym(handle, "Py_Initialize");
    Py_GetVersion = dlsym(handle, "Py_GetVersion");
    Py_Finalize = dlsym(handle, "Py_Finalize");

    // Check if symbols were successfully loaded
    if (!Py_Initialize || !Py_GetVersion || !Py_Finalize) {
        fprintf(stderr, "Failed to load Python functions: %s\n", dlerror());
        dlclose(handle);
        return 1;
    }

    // Call the Python API functions
    Py_Initialize();
    const char *version = Py_GetVersion();
    printf("Python version: %s\n", version);
    Py_Finalize();

    // Close the library
    dlclose(handle);

    return 0;
}
