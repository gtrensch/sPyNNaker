from spinn_machine.utilities.progress_bar import ProgressBar
from spinnman.messages.eieio.data_messages.eieio_data_header \
    import EIEIODataHeader

import numpy

import logging

logger = logging.getLogger(__name__)


class EIEIOSpikeRecorder(object):
    """ Records spikes using EIEIO format
    """

    def __init__(self):
        self._record = False

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, record):
        self._record = record

    def get_dtcm_usage_in_bytes(self):
        if not self._record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record:
            return 0
        return n_neurons * 4

    def get_spikes(self, label, buffer_manager, region,
                   placements, graph_mapper, application_vertex,
                   base_key_function, machine_time_step):

        results = list()
        missing_str = ""
        ms_per_tick = machine_time_step / 1000.0
        vertices = \
            graph_mapper.get_machine_vertices(application_vertex)
        progress_bar = ProgressBar(len(vertices),
                                   "Getting spikes for {}".format(label))

        for vertex in vertices:

            placement = placements.get_placement_of_vertex(vertex)
            vertex_slice = graph_mapper.get_slice(vertex)

            x = placement.x
            y = placement.y
            p = placement.p

            # Read the spikes
            raw_spike_data, data_missing = \
                buffer_manager.get_data_for_vertex(placement, region)
            if data_missing:
                missing_str += "({}, {}, {}); ".format(x, y, p)
            spike_data = str(raw_spike_data.read_all())
            number_of_bytes_written = len(spike_data)

            offset = 0
            while offset < number_of_bytes_written:
                eieio_header = EIEIODataHeader.from_bytestring(
                    spike_data, offset)
                offset += eieio_header.size
                timestamp = eieio_header.payload_base * ms_per_tick
                timestamps = numpy.repeat([timestamp], eieio_header.count)
                keys = numpy.frombuffer(
                    spike_data, dtype="<u4", count=eieio_header.count,
                    offset=offset)
                neuron_ids = ((keys - base_key_function(vertex)) +
                              vertex_slice.lo_atom)
                offset += eieio_header.count * 4
                results.append(numpy.dstack((neuron_ids, timestamps))[0])
            progress_bar.update()

        progress_bar.end()
        if len(missing_str) > 0:
            logger.warn(
                "Population {} is missing spike data in region {} from the"
                " following cores: {}".format(label, region, missing_str))
        if len(results) != 0:
            result = numpy.vstack(results)
            result = result[numpy.lexsort((result[:, 1], result[:, 0]))]
        else:
            result = []
        return result
