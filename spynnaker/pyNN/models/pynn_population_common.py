from spinn_front_end_common.abstract_models. \
    abstract_changable_after_run import AbstractChangableAfterRun
from spinn_front_end_common.utilities import exceptions


class PyNNPopulationCommon(object):
    def __init__(self, spinnaker_control, size, label, cellparams, cellclass):

        self._spinnaker_control = spinnaker_control
        self._vertex = None
        self._delay_vertex = None

        if size is not None and size <= 0:
            raise exceptions.ConfigurationException(
                "A population cannot have a negative or zero size.")

        # Create a graph vertex for the population and add it
        # to PACMAN
        cell_label = label
        if label is None:
            cell_label = "Population {}".format(
                spinnaker_control.none_labelled_vertex_count)
            spinnaker_control.increment_none_labelled_vertex_count()

        # copy the parameters so that the end users are not exposed to the
        # additions placed by spinnaker.
        internal_cellparams = dict(cellparams)

        # set spinnaker targeted parameters
        internal_cellparams['label'] = cell_label
        internal_cellparams['n_neurons'] = size

        # create population vertex.
        self._vertex = cellclass(**internal_cellparams)

    @property
    def requires_mapping(self):
        if isinstance(self._vertex, AbstractChangableAfterRun):
            return self._vertex.requires_mapping
        return self._change_requires_mapping

    def mark_no_changes(self):
        self._change_requires_mapping = False
        if isinstance(self._vertex, AbstractChangableAfterRun):
            self._vertex.mark_no_changes()