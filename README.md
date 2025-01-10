# OpenLedger Auto Send Heartbeat Bot 🤖

A Python bot for automatically managing OpenLedger heartbeat operations with multi-account and proxy support.

## ✨ Features

- 🔄 Automatic heartbeat sending
- 👥 Multi-account support
- 🔒 Proxy integration
- 📊 Real-time statistics and monitoring
- 🎨 Beautiful terminal interface with color-coded logs
- ⚡ Asynchronous operations for better performance
- 🔄 Automatic reconnection on connection loss
- 📈 Detailed runtime statistics

## 🔧 Requirements

- Python 3.7 or higher
- Required Python packages:
  - aiohttp
  - websockets

## 📥 Installation

1. Clone the repository:
```bash
git clone https://github.com/airdropinsiders/OpenLedger-Heartbeat-Bot.git
cd OpenLedger-Heartbeat-Bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your configuration files:
   - `account.txt`: Your account credentials
   - `proxy.txt`: List of proxies (optional)
   - `src/gpu.json`: GPU configurations

## ⚙️ Configuration

### How To Get Token,WorkerID,OwnerAddress
To get `Token`, `WorkerID`, `id` and `owneraddress` follow this steps:
- Register account first, you can [click here to register](https://testnet.openledger.xyz/?referral_code=ikurpd77ae)
- Download the [Extension](https://chromewebstore.google.com/detail/teneo-community-node/emcclcoaglgcpoognfiggmhnhgabppkm)
- Open Extension and right click and select `inspect`![no 1](https://github.com/user-attachments/assets/8abd970b-c1bc-44e1-b305-a9d76e7af063)

- Go to `network` tab![no 2](https://github.com/user-attachments/assets/4fa5e1ce-b49c-46c4-b70e-26307d465d62)

- Login to your account, and after login check the `network` tab again, search websocket connection `(orch?auth...)` and open![Screenshot 2025-01-10 022631](https://github.com/user-attachments/assets/a09ab2e5-7873-44c4-a3ce-26feb0ee1dd0)

- open `payload` tab and copy the `bearer/authtoken`![no 4](https://github.com/user-attachments/assets/1a14f452-ae2a-46e6-8d14-1a4d24ebd357)

- open `Messages` tab and copy the `WorkerID/identity`, `id` and `owneraddress` ![no 3](https://github.com/user-attachments/assets/ec6069e8-6a22-45cd-bdc5-ac9352b155f5)

### Account Format (`account.txt`)
Each line should contain account information in the following format:
```
token:workerID:id:ownerAddress
```

### Proxy Format (`proxy.txt`)
Each line should contain a single proxy in the following format:
```
protocol://ip:port
```
or
```
protocol://username:password@ip:port
```

### GPU Configuration (`src/gpu.json`)
JSON array containing available GPU models:
```json
[
  "NVIDIA GeForce RTX 3080",
  "NVIDIA GeForce RTX 3090",
  "AMD Radeon RX 6800 XT"
]
```

## 🚀 Usage

1. Make sure all configuration files are properly set up
2. Run the bot:
```bash
python main.py
```

3. Choose whether to use proxies when prompted

## 📊 Monitoring

The bot provides real-time information in the terminal:
- Account status and IDs
- Heartbeat confirmations
- Connection status
- Runtime statistics
- Error notifications

## 🎨 Terminal Display

The bot uses color-coded messages for different types of information:
- 🟦 Blue: System information
- 🟩 Green: Success messages
- 🟨 Yellow: Warnings and connections
- 🟥 Red: Errors and critical messages
- 🟦 Cyan: Account and session information

## ⚠️ Important Notes

1. Keep your account credentials secure and never share them
2. Using proxies is recommended to avoid IP restrictions
3. Make sure your proxies are stable and fast for optimal performance
4. Monitor the bot regularly to ensure proper operation

## 🔄 Auto-Restart (Optional)

To keep the bot running continuously, you can use a script like this:

```bash
#!/bin/bash
while true; do
    python main.py
    sleep 10
done
```

Save as `start.sh` and run:
```bash
chmod +x start.sh
./start.sh
```

## 📝 Logging

The bot logs all activities with timestamps and color coding:
- Connection attempts
- Heartbeat status
- Account updates
- Errors and warnings
- Runtime statistics

## 🛠 Troubleshooting

Common issues and solutions:

1. **Connection Errors**
   - Check your internet connection
   - Verify proxy settings if using proxies
   - Ensure account credentials are correct

2. **Authentication Failed**
   - Verify account tokens
   - Check if tokens have expired
   - Ensure proper formatting in account.txt

3. **High CPU Usage**
   - Reduce number of concurrent connections
   - Check proxy quality
   - Increase heartbeat intervals

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Community

- Join our Telegram group: [https://t.me/AirdropInsiderID](https://t.me/AirdropInsiderID)

## ⚠️ Disclaimer

This bot is for educational purposes only. Use at your own risk. The developers are not responsible for any misuse or damage caused by this program.
