from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models.abstract_contains_units import \
    AbstractContainsUnits
from spynnaker.pyNN.utilities import utility_calls
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type \
    import AbstractSynapseType

from data_specification.enums.data_type import DataType

import numpy
from enum import Enum


class _EXP_TYPES(Enum):

    E_DECAY = (1, DataType.UINT32)
    E_INIT = (2, DataType.UINT32)
    I_DECAY = (3, DataType.UINT32)
    I_INIT = (4, DataType.UINT32)
    INITIAL_EXC = (5, DataType.S1615)
    INITIAL_INH = (6, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


def get_exponential_decay_and_init(tau, machine_time_step):
    decay = numpy.exp(numpy.divide(-float(machine_time_step),
                                   numpy.multiply(1000.0, tau)))
    init = numpy.multiply(numpy.multiply(tau, numpy.subtract(1.0, decay)),
                          (1000.0 / float(machine_time_step)))
    scale = float(pow(2, 32))
    decay_scaled = numpy.multiply(decay, scale).astype("uint32")
    init_scaled = numpy.multiply(init, scale).astype("uint32")
    return decay_scaled, init_scaled


class SynapseTypeExponential(AbstractSynapseType, AbstractContainsUnits):
    def __init__(self, n_neurons, tau_syn_E, tau_syn_I,
                 initial_input_exc=0.0, initial_input_inh=0.0):
        AbstractSynapseType.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {
            'tau_syn_E': "mV",
            'tau_syn_I': 'mV',
            'gsyn_exc': "uS",
            'gsyn_inh': "uS"}

        self._n_neurons = n_neurons
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, n_neurons)
        self._tau_syn_I = utility_calls.convert_param_to_numpy(
            tau_syn_I, n_neurons)
        self._initial_input_exc = utility_calls.convert_param_to_numpy(
            initial_input_exc, n_neurons)
        self._initial_input_inh = utility_calls.convert_param_to_numpy(
            initial_input_inh, n_neurons)

    @property
    def tau_syn_E(self):
        return self._tau_syn_E

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._tau_syn_E = utility_calls.convert_param_to_numpy(
            tau_syn_E, self._n_neurons)

    @property
    def tau_syn_I(self):
        return self._tau_syn_I

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._tau_syn_I = utility_calls.convert_param_to_numpy(
            tau_syn_I, self._n_neurons)

    @property
    def isyn_exc(self):
        return self._initial_input_exc

    @isyn_exc.setter
    def isyn_exc(self, new_value):
        self._initial_input_exc = new_value

    @property
    def isyn_inh(self):
        return self._initial_input_inh

    @isyn_inh.setter
    def isyn_inh(self, new_value):
        self._initial_input_inh = new_value

    def get_n_synapse_types(self):
        return 2

    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "inhibitory":
            return 1
        return None

    def get_synapse_targets(self):
        return "excitatory", "inhibitory"

    def get_n_synapse_type_parameters(self):
        return 6

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_synapse_type_parameters(self, machine_time_step):
        e_decay, e_init = get_exponential_decay_and_init(
            self._tau_syn_E, machine_time_step)
        i_decay, i_init = get_exponential_decay_and_init(
            self._tau_syn_I, machine_time_step)

        return [
            NeuronParameter(e_decay, _EXP_TYPES.E_DECAY.data_type),
            NeuronParameter(e_init, _EXP_TYPES.E_INIT.data_type),
            NeuronParameter(i_decay, _EXP_TYPES.I_DECAY.data_type),
            NeuronParameter(i_init, _EXP_TYPES.I_INIT.data_type),
            NeuronParameter(
                self._initial_input_exc, _EXP_TYPES.INITIAL_EXC.data_type),
            NeuronParameter(
                self._initial_input_inh, _EXP_TYPES.INITIAL_INH.data_type)
        ]

    def get_synapse_type_parameter_types(self):
        return [item.data_type for item in _EXP_TYPES]

    def get_n_cpu_cycles_per_neuron(self):

        # A guess
        return 100

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
