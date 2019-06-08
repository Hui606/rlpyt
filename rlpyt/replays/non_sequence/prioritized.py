
from rlpyt.replays.non_sequence.n_step import NStepReturnBuffer, SamplesFromReplay
from rlpyt.replays.sum_tree import SumTree
from rlpyt.utils.collections import namedarraytuple
from rlpyt.utils.quick_args import save__init__args
from rlpyt.utils.buffer import torchify_buffer


SamplesFromReplayPri = namedarraytuple("SamplesFromReplayPri",
    SamplesFromReplay._fields + ("is_weights",))


class PrioritizedReplayBuffer(NStepReturnBuffer):

    def __init__(self, alpha, beta, default_priority, unique=False, **kwargs):
        super().__init__(**kwargs)
        save__init__args(locals())
        self.init_priority_tree()

    def init_priority_tree(self):
        """Organized here for clean inheritance."""
        self.priority_tree = SumTree(
            T=self.T,
            B=self.B,
            off_backward=self.off_backward,
            off_forward=self.off_forward,
            default_value=self.default_priority ** self.alpha,
        )

    def set_beta(self, beta):
        self.beta = beta

    def append_samples(self, samples):
        T = super().append_samples(samples)
        self.priority_tree.advance(T)  # Progress priority_tree cursor.

    def sample_batch(self, batch_size):
        (T_idxs, B_idxs), priorities = self.priority_tree.sample(batch_size,
            unique=self.unique)
        batch = self.extract_batch(T_idxs, B_idxs)
        is_weights = (1. / priorities) ** self.beta  # Unnormalized.
        is_weights /= max(is_weights)  # Normalize.
        return SamplesFromReplayPri(*batch, is_weights=torchify_buffer(is_weights))

    def update_batch_priorities(self, priorities):
        self.priority_tree.update_batch_priorities(priorities ** self.alpha)