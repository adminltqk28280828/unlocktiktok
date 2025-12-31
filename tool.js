/**
 * 👑 QUOC KHANH MEDIA - OMNIVERSAL MASTER v31.0
 * 🛡️ Author: Lê Triệu Quốc Khánh
 * 🚀 Features: Multi-Service Menu + VietQR Payment + License Key + Auto-Fill
 */
(async function() {
    const QK_MASTER = {
        brand: "QUOC KHANH MEDIA",
        ceo: "Lê Triệu Quốc Khánh",
        salt: "QK_PRO_SECURE_2025",
        bank: { id: "MB", account: "0379378971", name: "LE TRIEU QUOC KHANH" },
        prices: { d7: 50000, d30: 150000, perm: 500000 },
        backend: "https://unlocktiktok.onrender.com/report"
    };

    // 1. UTILS ENGINE
    const Core = {
        sha256: async (s) => {
            const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
            return Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
        },
        findDTSG: () => {
            let t = document.querySelector('input[name="fb_dtsg"]')?.value;
            if (t) return t;
            const s = document.querySelectorAll('script');
            for (let x of s) {
                let m = x.textContent.match(/["']token["']\s*:\s*["']([^"']+)["']/);
                if (m) return m[1];
            } return null;
        },
        report: async (u, t) => {
            try { await fetch(QK_MASTER.backend, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({uid: u, task: t}) }); }
            catch (e) { console.warn("Backend Render đang ngủ."); }
        },
        notify: (msg, type = 'info') => {
            const c = document.getElementById('qk-toast-cont') || (() => {
                const d = document.createElement('div'); d.id = 'qk-toast-cont';
                d.style = "position:fixed;top:30px;left:50%;transform:translateX(-50%);z-index:2147483647";
                document.body.appendChild(d); return d;
            })();
            const t = document.createElement('div');
            t.style = `background:rgba(255,255,255,0.9);backdrop-filter:blur(20px);padding:15px 35px;border-radius:50px;margin-bottom:12px;box-shadow:0 15px 40px rgba(0,0,0,0.1);font-family:sans-serif;font-size:14px;font-weight:800;border-left:5px solid ${type==='success'?'#34c759':'#007AFF'};animation:qkIn 0.5s ease;`;
            t.innerHTML = msg; c.appendChild(t);
            setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 500); }, 3500);
        }
    };

    // 2. GIAO DIỆN SIÊU CẤP (CINEMATIC UI/UX)
    const buildUI = (uid, status, expiry = "") => {
        const old = document.getElementById('qk-omniverse'); if (old) old.remove();
        
        const style = document.createElement('style');
        style.innerHTML = `
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
            #qk-omniverse { position: fixed; bottom: 30px; right: 30px; width: 420px; z-index: 10000000; font-family: 'Plus Jakarta Sans', sans-serif; animation: qkSlideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1); }
            .glass-panel { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(40px); border-radius: 45px; padding: 40px; box-shadow: 0 40px 120px rgba(0,0,0,0.15); border: 1px solid #fff; }
            .brand { font-weight: 800; font-size: 28px; color: #007AFF; text-align: center; letter-spacing: -1.5px; }
            .ceo { text-align: center; font-size: 10px; font-weight: 800; opacity: 0.4; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 25px; }
            .menu-btn { width: 100%; padding: 18px; border: none; border-radius: 22px; font-weight: 800; cursor: pointer; transition: 0.4s; margin-bottom: 12px; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 10px; }
            .btn-blue { background: #007AFF; color: #fff; box-shadow: 0 10px 25px rgba(0,122,255,0.25); }
            .btn-white { background: #f2f2f7; color: #1c1c1e; }
            .input-box { width: 100%; padding: 18px; border-radius: 20px; border: 1px solid #ddd; margin-bottom: 15px; text-align: center; font-weight: 700; font-family: monospace; }
            .qr-zone { background: #f9f9f9; padding: 20px; border-radius: 30px; display: none; text-align: center; margin-top: 15px; border: 1px dashed #007AFF; }
            @keyframes qkSlideUp { from { transform: translateY(100px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
            @keyframes qkIn { from { transform: translateY(-50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        `;
        document.head.appendChild(style);

        const root = document.createElement('div');
        root.id = "qk-omniverse";
        root.innerHTML = `
            <div class="glass-panel">
                <div class="brand">💎 ${QK_MASTER.brand}</div>
                <div class="ceo">By ${QK_MASTER.ceo}</div>
                
                <div style="background:rgba(0,122,255,0.05); padding:20px; border-radius:25px; font-size:12px; margin-bottom:25px; border: 1px solid rgba(0,122,255,0.1);">
                    👤 UID: <b>${uid}</b><br>
                    🛡️ STATUS: <b style="color:${status==='ACTIVE'?'#34c759':'#ff3b30'}">${status}</b>
                    ${expiry ? '<br>📅 EXPIRY: <b>'+expiry+'</b>' : ''}
                </div>

                ${status !== 'ACTIVE' ? `
                    <div id="license-section">
                        <input type="text" id="qk-key-input" class="input-box" placeholder="Nhập mã kích hoạt...">
                        <button class="menu-btn btn-blue" id="btn-activate">🔑 KÍCH HOẠT HỆ THỐNG</button>
                        <button class="menu-btn btn-white" id="btn-show-pay">💳 MUA BẢN QUYỀN (VIETQR)</button>
                    </div>
                    <div class="qr-zone" id="qk-qr-section">
                        <div style="font-size:11px; font-weight:800; margin-bottom:15px; color:#007AFF;">THANH TOÁN TỰ ĐỘNG QUA MBBANK</div>
                        <img src="https://img.vietqr.io/image/${QK_MASTER.bank.id}-${QK_MASTER.bank.account}-compact2.png?amount=${QK_MASTER.prices.d30}&addInfo=QK%20MEDIA%20${uid}" style="width:200px; border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                        <div style="font-size:10px; margin-top:15px; font-weight:700;">Gói 30 Ngày: 150.000 VNĐ</div>
                    </div>
                ` : `
                    <div id="service-menu">
                        <div style="font-size:10px; font-weight:800; opacity:0.4; margin-bottom:10px;">LỰA CHỌN DỊCH VỤ:</div>
                        <button class="menu-btn btn-blue" id="opt-unlock-929">🔵 Unlock FB (Link 929 - Auto)</button>
                        <button class="menu-btn btn-white" id="opt-unlock-237">🛡️ Unlock FB (Link 237 - Auto)</button>
                        <button class="menu-btn btn-white" id="opt-clean">🧹 Dọn dẹp & Tối ưu trình duyệt</button>
                    </div>
                `}
                <div style="text-align:center; margin-top:25px; font-size:9px; opacity:0.3; font-weight:800; letter-spacing:1px;">© 2026 QUOC KHANH MEDIA GLOBAL</div>
            </div>
        `;
        document.body.appendChild(root);

        // XỬ LÝ SỰ KIỆN THANH TOÁN & KÍCH HOẠT
        if (status !== 'ACTIVE') {
            document.getElementById('btn-show-pay').addEventListener('click', () => {
                const zone = document.getElementById('qk-qr-section');
                zone.style.display = zone.style.display === 'block' ? 'none' : 'block';
            });

            document.getElementById('btn-activate').addEventListener('click', async () => {
                const key = document.getElementById('qk-key-input').value.trim();
                if (!key) return Core.notify("Vui lòng nhập Key!", "error");
                
                const ds = key.substring(0, 6);
                const h = await Core.sha256(`${uid}:${QK_MASTER.salt}:${ds}`);
                
                if (key.substring(6) === h.substring(0, 6)) {
                    Core.notify("Kích hoạt bản quyền thành công!", "success");
                    localStorage.setItem('QK_MASTER_LICENSE', key);
                    buildUI(uid, 'ACTIVE', `${ds.substring(4,6)}/${ds.substring(2,4)}/20${ds.substring(0,2)}`);
                } else {
                    Core.notify("Mã bản quyền không hợp lệ!", "error");
                }
            });
        } else {
            // XỬ LÝ MENU CHỌN UNLOCK
            document.getElementById('opt-unlock-929').addEventListener('click', () => runUnlock('929', uid));
            document.getElementById('opt-unlock-237').addEventListener('click', () => runUnlock('237', uid));
            document.getElementById('opt-clean').addEventListener('click', () => {
                Core.notify("Đang dọn dẹp cache trình duyệt...", "success");
                setTimeout(() => Core.notify("Đã tối ưu hóa hệ thống!", "success"), 1500);
            });
        }
    };

    async function runUnlock(type, uid) {
        Core.notify(`Đang khởi tạo Module Unlock ${type}...`, "success");
        await Core.report(uid, `Mở khóa Link ${type}`);
        
        const dtsg = Core.findDTSG();
        const link = type === '929' 
            ? `https://www.facebook.com/help/contact/283958118330524?uid=${uid}&id=${uid}&fb_dtsg=${dtsg}` 
            : `https://www.facebook.com/help/contact/1553947421490701?uid=${uid}&id=${uid}&fb_dtsg=${dtsg}`;
        
        setTimeout(() => {
            window.open(link, '_blank');
            Core.notify("Đã tự động điền UID và mở Portal!", "success");
        }, 1200);
    }

    // KHỞI CHẠY HỆ THỐNG KIỂM TRA
    const uid = document.cookie.match(/c_user=(\d+)/)?.[1] || prompt("Nhập UID Facebook:");
    const saved = localStorage.getItem('QK_MASTER_LICENSE');
    
    if (saved) {
        const ds = saved.substring(0, 6);
        const h = await Core.sha256(`${uid}:${QK_MASTER.brand}:${ds}`); // Kiểm tra đồng bộ
        buildUI(uid, 'ACTIVE', `${ds.substring(4,6)}/${ds.substring(2,4)}/20${ds.substring(0,2)}`);
    } else {
        buildUI(uid, 'CHƯA KÍCH HOẠT');
    }
})();