# Colab And SSH Notes

## Important Policy Caveat

Google Colab's FAQ explicitly says that remote control use cases such as `SSH shells` and `remote desktops` are disallowed on free managed runtimes and may be terminated at any time. Those restrictions can be relaxed on paid plans with positive compute balance, or by using your own compute via a local runtime or dedicated VM.

Practical takeaway:

- free Colab: not reliable for SSH-style access
- paid Colab: more viable, still not as stable as a normal VM
- best option for shell access: a dedicated GPU VM over normal `SSH`

## Recommended Colab Workflow

Use Colab primarily as a notebook runtime:

1. mount Drive
2. point the notebook at your dataset and project files
3. run the training and eval cells
4. send logs and outputs back for debugging

That is the lowest-friction path.

## If You Still Want SSH-Style Access In Colab

These are the common approaches people use.

### 1. `tmate`

Good for quick temporary shell sharing.

Typical pattern in Colab:

```bash
!apt-get -qq install -y tmate openssh-server
!tmate -F
```

Then retrieve the session string:

```bash
!tmate display -p '#{tmate_ssh}'
```

Notes:

- simplest ad hoc option
- session is ephemeral
- depends on Colab runtime staying alive
- can get killed by Colab policy/runtime behavior

### 2. `cloudflared`

Useful if you already use Cloudflare Tunnel.

Typical pattern:

1. install and start `openssh-server`
2. install `cloudflared`
3. create a tunnel to local port `22`

Example shape:

```bash
!apt-get -qq install -y openssh-server
!service ssh start
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
!cloudflared tunnel --url ssh://localhost:22
```

Notes:

- cleaner than random port forwarding if you already have Cloudflare set up
- better fit for users already familiar with Tunnels
- still subject to Colab runtime limits

### 3. `ngrok`

Common tunnel approach if you already have an auth token.

Typical pattern:

```bash
!apt-get -qq install -y openssh-server
!service ssh start
!curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
!echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list
!apt-get update
!apt-get install -y ngrok
!ngrok config add-authtoken YOUR_TOKEN
!ngrok tcp 22
```

Notes:

- easy if you already use `ngrok`
- requires your auth token
- session address changes unless you have a reserved setup

## Safer Alternative

If you want stable remote shell access for repeated training runs, use one of these instead of Colab SSH:

- RunPod
- Vast.ai
- Lambda
- Paperspace
- any Ubuntu GPU VM with normal `SSH`

## What I Added To This Repo

- `notebooks/olmocr_table_html_colab.ipynb`: Colab-ready notebook
- `scripts/train_table_html_lora.py`: training entrypoint
- `scripts/eval_table_structure.py`: structural evaluation helper
- `examples/table_html_dataset.example.jsonl`: dataset schema example

## Sources Used

- Google Colab FAQ: remote control such as SSH shells are disallowed on free managed runtimes
- `tmate` project: terminal sharing workflow
- `cloudflared` docs/repo: tunnel client for SSH/TCP forwarding
- `ngrok` docs: SSH/RDP and TCP tunnel support
