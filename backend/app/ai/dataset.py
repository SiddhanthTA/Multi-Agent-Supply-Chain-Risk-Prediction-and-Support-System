import torch
from torch.utils.data import Dataset


# --------------------------------------------------
# Custom Dataset for DistilBERT
# --------------------------------------------------

class SupplyChainDataset(Dataset):

    def __init__(self, encodings, labels):
        """
        Parameters
        ----------
        encodings : dict
            Output from DistilBERT tokenizer.

        labels : list
            Encoded category labels.
        """

        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        """
        Returns the total number of samples.
        """
        return len(self.labels)

    def __getitem__(self, idx):
        """
        Returns one training sample.
        """

        item = {
            key: torch.tensor(value[idx])
            for key, value in self.encodings.items()
        }

        item["labels"] = torch.tensor(self.labels[idx])

        return item