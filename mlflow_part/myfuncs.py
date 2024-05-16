import torch
import pandas as pd
import myconfig
from tqdm import tqdm

def load_checkpoint(checkpoint,model,optimizer,lr):
    print("Loading checkpoint...")
    model.load_state_dict(checkpoint["state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer"])

    for param_group in optimizer.param_groups:
        param_group["lr"] = lr

def save_checkpoint(state,filename='checkpt.pth.tar'):
    print("Saving checkpoint...")
    torch.save(state,filename)

def get_submission(loader, dataset, model):
    model.eval()
    predictions = pd.DataFrame()
    image_id = 1

    for image, label in tqdm(loader):
        image = image.to(myconfig.DEVICE)
        preds = torch.clip(model(image).squeeze(0), 0.0, 96.0)
        predictions = pd.concat([predictions,pd.Series(preds.detach().numpy()).to_frame().T],ignore_index=True)

        image_id += 1

    predictions.to_csv("submission.csv", index=False)
    model.train()

def get_rmse(loader, model, loss_fn, device):
    model.eval()
    num_examples = 0
    losses = []
    for batch_idx, (data, targets) in enumerate(loader):
        data = data.to(device=device)
        targets = targets.to(device=device)

        scores = model(data)
        loss = loss_fn(scores[targets != -1], targets[targets != -1])
        num_examples += scores[targets != -1].shape[0]
        losses.append(loss.item())

    model.train()
    print(f"Loss on val: {(sum(losses)/num_examples)**0.5}")
    return (sum(losses)/num_examples)**0.5