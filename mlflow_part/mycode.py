from mydatasetclass import FacialKeypointDataset
import myconfig
from tqdm import tqdm
import torch
from torch.utils.data import DataLoader,Dataset
from efficientnet_pytorch import EfficientNet
from torch import nn,optim
import os
from myfuncs import load_checkpoint,get_rmse,get_submission,save_checkpoint

print(os.getcwd())

def train_one_epoch(loader, model, optimizer, loss_fn, scaler, device):
    losses = []
    loop = tqdm(loader)
    num_examples = 0
    for batch_idx, (data, targets) in enumerate(loop):
        data = data.to(device=device)
        targets = targets.to(device=device)

        scores = model(data)
        scores[targets == -1] = -1
        loss = loss_fn(scores, targets)
        num_examples += torch.numel(scores[targets != -1])
        losses.append(loss.item())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    print(f"Loss average over epoch: {(sum(losses)/num_examples)**0.5}")

def main():
    train_ds = FacialKeypointDataset(
        csv_file="/Users/nikhilanand/JupyterNotebooks/InterIIT2023/CVSelections/training_new.csv",
        transform=myconfig.train_transforms
    )
    train_loader = DataLoader(
        train_ds,
        batch_size=myconfig.BATCH_SIZE,
        num_workers=myconfig.NUM_WORKERS,
        pin_memory=myconfig.PIN_MEMORY,
        shuffle=True
    )
    val_ds = FacialKeypointDataset(
        transform=myconfig.val_transforms,
        csv_file="/Users/nikhilanand/JupyterNotebooks/InterIIT2023/CVSelections/val_new.csv"
    )
    val_loader=DataLoader(
        val_ds,
        batch_size=myconfig.BATCH_SIZE,
        num_workers=myconfig.NUM_WORKERS,
        pin_memory=myconfig.PIN_MEMORY,
        shuffle=False
    )
    test_ds = FacialKeypointDataset(
        csv_file="/Users/nikhilanand/JupyterNotebooks/InterIIT2023/CVSelections/test.csv",
        transform=myconfig.val_transforms,
        train=False,
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=1,
        num_workers=myconfig.NUM_WORKERS,
        pin_memory=myconfig.PIN_MEMORY,
        shuffle=False,
    )

    loss_fn = nn.MSELoss(reduction="sum")
    model = EfficientNet.from_pretrained("efficientnet-b0")
    model._fc = nn.Linear(1280, 30)
    model = model.to(myconfig.DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=myconfig.LEARNING_RATE, weight_decay=myconfig.WEIGHT_DECAY)
    scaler = torch.cuda.amp.GradScaler()
    if myconfig.LOAD_MODEL and myconfig.CHECKPOINT_FILE in os.listdir():
        load_checkpoint(torch.load(myconfig.CHECKPOINT_FILE), model, optimizer, myconfig.LEARNING_RATE)

    get_submission(test_loader, test_ds, model)
    print("Got submission")

    for epoch in range(myconfig.NUM_EPOCHS):
        get_rmse(val_loader, model, loss_fn, myconfig.DEVICE)
        train_one_epoch(train_loader, model, optimizer, loss_fn, scaler, myconfig.DEVICE)

        if myconfig.SAVE_MODEL:
            checkpoint = {
                "state_dict": model.state_dict(),
                "optimizer": optimizer.state_dict(),
            }
            save_checkpoint(checkpoint, filename=myconfig.CHECKPOINT_FILE)

if __name__ == "__main__":
    main()
