apt install tmux
tmux new-session -d python3 run.py
git clone https://github.com/ryleu/revolt-dice-bot
cd revolt-dice-bot
tmux new-session -d python3 run.py
