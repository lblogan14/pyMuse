from queue import Queue

from pymuse.pipelinestages.pipeline_stage import PipelineStage
from pymuse.signal import Signal
from pymuse.constants import PIPELINE_QUEUE_SIZE


class PipelineFork():
    def __init__(self, *branches):
        self.forked_branches: list = list(branches)


class Pipeline():

    def __init__(self, input_signal: Signal, *stages):
        """ E.g.: Pipeline(Signal(), PipelineStage(), PipelineFork([PipelineStage(), PipelineStage()], [PipelineStage()] )) """
        self._output_queues = []
        self._input_signal = input_signal
        self._stages: list = list(stages)
        self._link_stages(self._stages)
        self._stages[0]._queue_in = self._input_signal.signal_queue

    def get_output_queue(self, queue_index=0) -> Queue:
        """Return a ref to the queue given by queue_index"""
        return self._output_queues[queue_index]

    def read_output_queue(self, queue_index=0):
        """Wait to read a data in a queue given by queue_index"""
        return self._output_queues[queue_index].get()

    def start(self):
        """Start all pipelines stages."""
        self._start(self._stages)

    def shutdown(self):
        """ shutdowns every child thread (PipelineStage)"""
        self._shutdown(self._stages)

    def join(self):
        """Ensure every thread (PipelineStage) of the pipeline are done"""
        for stage in self._stages:
            stage.join()

    def _link_pipeline_fork(self, stages: list, index: int):
        for fork in stages[index].forked_branches:
            stages[index - 1].add_queue_out(fork[0].queue_in)
            self._link_stages(fork)

    def _link_stages(self, stages: list):
        for i in range(1, len(stages)):
            if type(stages[i]) == PipelineFork:
                self._link_pipeline_fork(stages, i)
            else:
                stages[i - 1].add_queue_out(stages[i].queue_in)
        if issubclass(type(stages[-1]), PipelineStage):
            output_queue = Queue(PIPELINE_QUEUE_SIZE)
            stages[-1].add_queue_out(output_queue)
            self._output_queues.append(output_queue)

    def _start(self, stages: list):
        for stage in stages:
            if type(stage) == PipelineFork:
                for forked_branch in stage.forked_branches:
                    self._start(forked_branch)
            else:
                stage.start()

    def _shutdown(self, stages: list):
        for stage in stages:
            if type(stage) == PipelineFork:
                for forked_branch in stage.forked_branches:
                    self._shutdown(forked_branch)
            else:
                stage.shutdown()
