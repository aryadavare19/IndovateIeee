from datasets import load_dataset
from PIL import Image
import os
from torchvision import transforms

dataset = load_dataset("Simezu/brain-tumour-MRI-scan")

print(dataset)
