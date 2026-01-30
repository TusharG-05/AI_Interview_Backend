# SSL Configuration & Local Testing Guide

This guide explains how to handle SSL certificates for local testing, which is required by modern browsers (Chrome, Safari, Firefox) to access the **Camera and Microphone** on non-localhost origins.

## 1. Using Self-Signed Certificates (Quickest)

By default, this project uses self-signed certificates (`cert.pem` and `key.pem`).

### For Desktop Browsers (Chrome/Edge)
When you visit `https://<YOUR_IP>:8000`:
1. You will see a "Your connection is not private" warning.
2. Click **Advanced**.
3. Click **Proceed to <your-ip> (unsafe)**.

### For Mobile Browsers (iOS Safari / Android Chrome)
Browsers on mobile are stricter. You may need to manually "trust" the certificate:
1. **iOS**: Send the `cert.pem` to your phone (Email/AirDrop). Open it in **Settings > Profile Downloaded** to install. Then go to **Settings > General > About > Certificate Trust Settings** and toggle on full trust for the root certificate.
2. **Chrome (Android)**: Similar to iOS, install the certificate via **Settings > Security > More Settings > Encryption & Credentials > Install from storage**.

---

## 2. Using Ngrok (Easiest for Mobile)

If you don't want to deal with certificate warnings, use **Ngrok** to create a secure tunnel with a valid SSL certificate.

1. **Install Ngrok**: [ngrok.com](https://ngrok.com/)
2. **Start the Backend**: Run the app normally (even without local SSL).
3. **Open a Tunnel**:
   ```bash
   ngrok http 8000
   ```
4. **Access the URL**: Ngrok will provide an `https://xxxx.ngrok-free.app` URL. This URL is recognized as "Secure" by all browsers, enabling the camera/mic immediately without any warnings.

---

## 3. Regenerating Certificates

If your certificates expire or you change your local IP:
```bash
python3 tools/generate_cert.py
```
This script generates a new 2048-bit RSA key and a self-signed certificate valid for 365 days.

---

## Troubleshooting

- **Camera not starting**: Ensure you are using `https://`. Most browsers block `navigator.mediaDevices` on plain `http://` for security.
- **Connection Refused**: Ensure the backend is running and the port (8000) is open in your firewall.
- **Docker Access**: If accessing from another device, ensure the `compose.yaml` maps the port correctly (e.g., `8000:8000`).
