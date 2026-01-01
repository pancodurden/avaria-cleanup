const scanBtn = document.getElementById('scan-btn');
const cleanBtn = document.getElementById('clean-btn');
const statusCircle = document.getElementById('status-circle');
const dataDisplay = document.getElementById('data-display');
const logArea = document.getElementById('log-area');
const systemInfo = document.getElementById('system-info');

let eventSource;

function taramayiBaslat() {
    logArea.innerText = "> Bağlantı kuruluyor...";
    scanBtn.disabled = true;
    cleanBtn.disabled = true;
    statusCircle.className = "circle scanning";

    if (eventSource) eventSource.close();

    // EventSource Flask'tan gelen veriyi dinler
    eventSource = new EventSource('/stream/tara');

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);

        if (data.tip === "info") {
            systemInfo.innerText = "Sistem: " + data.os;
        } 
        else if (data.tip === "progress") {
            dataDisplay.innerText = data.toplam_gb;
            logArea.innerHTML = `> Taraniyor: <span style="color:#fff">${data.dosya}</span>`;
        } 
        else if (data.tip === "done") {
            eventSource.close();
            scanBtn.disabled = false;
            cleanBtn.disabled = false;
            logArea.innerText = "> ANALİZ TAMAMLANDI.";
            statusCircle.className = "circle danger";
        }
    };

    eventSource.onerror = function() {
        if (eventSource.readyState !== 2) {
            logArea.innerText = "> HATA: Bağlantı koptu.";
            eventSource.close();
            scanBtn.disabled = false;
            statusCircle.className = "circle";
        }
    };
}

async function temizligiBaslat() {
    if(!confirm("Dosyalar kalıcı olarak silinecek. Onaylıyor musun?")) return;
    
    logArea.innerText = "> Temizlik protokolü devrede...";
    cleanBtn.disabled = true;
    
    try {
        const response = await fetch('/api/temizle');
        const data = await response.json();
        
        logArea.innerText = `> İŞLEM BAŞARILI. ${data.silinen} dosya silindi.`;
        alert(`Sistem Rahatladı! Toplam ${data.kazanc} GB çöp silindi.`);
        
        dataDisplay.innerText = "0.000";
        statusCircle.className = "circle";
        statusCircle.style.borderColor = "#00ff41";
        
    } catch (e) {
        logArea.innerText = "> SİLME HATASI.";
    }
}