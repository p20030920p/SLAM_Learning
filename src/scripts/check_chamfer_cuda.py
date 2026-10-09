"""Exercise the exact CUDA KNN operation required by the original evaluator."""
import json
import hashlib
from pathlib import Path
import torch
from chamferdist import _C
from chamferdist.chamfer import knn_points

assert torch.cuda.is_available() and hasattr(_C,'knn_check_version')
query=torch.tensor([[[0.1,0,0],[1.9,0,0]]],dtype=torch.float32,device='cuda')
reference=torch.tensor([[[0.,0,0],[2.,0,0]]],dtype=torch.float32,device='cuda')
result=knn_points(query,reference,K=1)
torch.cuda.synchronize()
assert result.idx.reshape(-1).tolist()==[0,1]
assert torch.allclose(result.dists,torch.full_like(result.dists,0.01),atol=1e-6)
print(json.dumps({'status':'passed','operation':'chamferdist CUDA KNN, K=1',
    'indices':result.idx.cpu().tolist(),'squared_distances':result.dists.cpu().tolist(),
    'extension':_C.__file__,'extension_sha256':hashlib.sha256(Path(_C.__file__).read_bytes()).hexdigest(),
    'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0)}),flush=True)
