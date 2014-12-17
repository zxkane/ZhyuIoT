#include <Python.h>

#include "Raspberry_Pi/pi_gp2y10_read.h"

// Wrap calling gp2y10_read function and expose it as a GP2Y10.read Python module & function.
static PyObject* Raspberry_Pi_Driver_read(PyObject *self, PyObject *args)
{
	// Parse sensor and pin integer arguments.
    int sensor, sample;
    if (!PyArg_ParseTuple(args, "ii", &sensor, &sample)) {
        return NULL;
    }
    // Call dht_read and return result code, duster density.
    float density = 0;
    int result = pi_gp2y10_read(sensor, sample, &density);
    return Py_BuildValue("if", result, density);
}

// Boilerplate python module method list and initialization functions below.

static PyMethodDef module_methods[] = {
    {"read", Raspberry_Pi_Driver_read, METH_VARARGS, "Read GP2Y10 sensor value on a Raspberry Pi."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initRaspberry_Pi_Driver(void)
{
    Py_InitModule("Raspberry_Pi_Driver", module_methods);
}
