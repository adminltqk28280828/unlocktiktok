/**
 * 🚀 QUOC KHANH MEDIA - ULTIMATE WORKSPACE v17.0
 * Full Features: Auto Link + Telegram Report + Luxury UI
 * Security: SHA-256 Sync | Fix CSP Facebook
 */
(async function() {
    // 1. CẤU HÌNH HỆ THỐNG (ĐỒNG BỘ VỚI BOT TELEGRAM)
    const QK_CONFIG = {
        brand: "QUOC KHANH MEDIA",
        salt: "QK_PRO_SECURE_2025", 
        botToken: "8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw", // Token của Khánh
        adminId: "6684980246", // ID của Khánh
        support: "https://zalo.me/0379378971",
        version: "17.0 Ultimate"
    };

    // 2. TIỆN ÍCH HỆ THỐNG
    const Utils = {
        // Quét mã xác thực DTSG trên Facebook
        findDTSG: () => {
            let t = document.querySelector('input[name="fb_dtsg"]')?.value;
            if (t) return t;
            const scripts = document.querySelectorAll('script');
            for (let s of scripts) {
                let m = s.textContent.match(/["']token["']\s*:\s*["']([^"']+)["']/);
                if (m) return m[1];
            }
            return null;
        },
        // Mã hóa SHA-256 đồng bộ với Python hashlib
        sha256: async (str) => {
            const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
            return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();
        },
        // GỬI THÔNG TIN VỀ TELEGRAM ADMIN
        notifyAdmin: async (uid, task) => {
            const text = `🚀 **QK MEDIA - BÁO CÁO MỚI**\n━━━━━━━━━━━━━━━━━━\n👤 **Khách hàng:** \`${uid}\`\n🛠️ **Hành động:** ${task}\n⏰ **Thời gian:** ${new Date().toLocaleString('vi-VN')}\n━━━━━━━━━━━━━━━━━━`;
            const url = `https://api.telegram.org/bot${QK_CONFIG.botToken}/sendMessage?chat_id=${QK_CONFIG.adminId}&text=${encodeURIComponent(text)}&parse_mode=Markdown`;
            try { await fetch(url); } catch (e) { console.error("Lỗi báo cáo:", e); }
        }
    };

    // 3. GIAO DIỆN SIÊU CẤP (GLASSMORPHISM UI)
    const injectUI = (uid, expiry) => {
        const style = document.createElement('style');
        style.innerHTML = `
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
            #qk-os {
                position: fixed; top: 30px; right: 30px; width: 380px; z-index: 2147483647;
                font-family: 'Plus Jakarta Sans', sans-serif; animation: qkIn 0.6s cubic-bezier(0.2, 1, 0.2, 1);
            }
            .glass {
                background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px);
                border-radius: 35px; padding: 25px; box-shadow: 0 25px 60px rgba(0,0,0,0.1); border: 1px solid #fff;
            }
            .qk-logo { font-weight: 800; font-size: 22px; color: #007AFF; text-align: center; margin-bottom: 20px; }
            .qk-btn {
                width: 100%; padding: 14px; margin: 8px 0; border: none; border-radius: 18px;
                font-weight: 700; cursor: pointer; transition: 0.3s; font-size: 14px;
            }
            .btn-blue { background: #007AFF; color: #fff; box-shadow: 0 4px 15px rgba(0,122,255,0.3); }
            .btn-white { background: #f2f2f7; color: #1c1c1e; }
            .qk-console {
                background: #000; border-radius: 15px; padding: 12px; margin-top: 15px;
                font-family: monospace; font-size: 10px; color: #32d74b; height: 100px; overflow-y: auto;
            }
            @keyframes qkIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        `;
        document.head.appendChild(style);

        const root = document.createElement('div');
        root.id = "qk-os";
        root.innerHTML = `
            <div class="glass">
                <div class="qk-logo">💎 QK MEDIA</div>
                <div style="font-size:12px; text-align:center; margin-bottom:15px;">🛡️ UID: ${uid} | 📅 Hạn: ${expiry}</div>
                <button class="qk-btn btn-blue" id="btn-fb">🔵 Mở khóa Facebook PRO</button>
                <button class="qk-btn btn-white" id="btn-tk">📱 Mở khóa TikTok PRO</button>
                <button class="qk-btn btn-white" id="btn-support">📞 Hỗ trợ Zalo</button>
                <div class="qk-console" id="qk-logs">> Hệ thống Enterprise v17.0 sẵn sàng...</div>
            </div>
        `;
        document.body.appendChild(root);

        // LẮNG NGHE SỰ KIỆN (FIX LỖI CSP)
        document.getElementById('btn-fb').addEventListener('click', () => runUnlock('Facebook', uid));
        document.getElementById('btn-tk').addEventListener('click', () => runUnlock('TikTok', uid));
        document.getElementById('btn-support').addEventListener('click', () => window.open(QK_CONFIG.support));
    };

    async function runUnlock(type, uid) {
        const log = document.getElementById('qk-logs');
        log.innerHTML += `<div>> Khởi tạo Module ${type}...</div>`;
        
        const dtsg = Utils.findDTSG();
        if (!dtsg) return alert("❌ Lỗi: Không tìm thấy DTSG. Hãy F5 trang!");

        // 🚀 TÍNH NĂNG NÂNG CẤP: BÁO CÁO VỀ TELEGRAM ADMIN
        log.innerHTML += `<div>> Đang gửi báo cáo về Telegram Admin...</div>`;
        await Utils.notifyAdmin(uid, `Yêu cầu Mở khóa ${type}`);
        
        log.innerHTML += `<div style="color:#007AFF">> Đã báo cáo thành công! Đang tạo link...</div>`;

        setTimeout(() => {
            // Tạo link kháng nghị chuẩn giống code gốc
            const link = `https://www.facebook.com/help/contact/283958118330524?uid=${uid}&dtsg=${dtsg}`;
            window.open(link, '_blank');
            log.innerHTML += `<div style="color:#32d74b">> Hoàn tất! Link đã được mở.</div>`;
        }, 1500);
    }

    // 4. KIỂM TRA BẢN QUYỀN (AUTHENTICATION)
    const uid = document.cookie.match(/c_user=(\d+)/)?.[1] || prompt("Nhập UID Facebook:");
    if (!uid) return;

    const key = prompt(`💎 ${QK_CONFIG.brand}\nNhập mã kích hoạt cho UID ${uid}:`);
    const dateStr = key.substring(0, 6);
    const hash = await Utils.sha256(`${uid}:${QK_CONFIG.salt}:${dateStr}`);

    if (key.substring(6) === hash.substring(0, 6)) {
        injectUI(uid, `${dateStr.substring(4,6)}/${dateStr.substring(2,4)}/20${dateStr.substring(0,2)}`);
    } else {
        alert("❌ Mã kích hoạt không chính xác!");
    }
})();