const fileInput = document.getElementById('fileInput');
const fileLabelText = document.getElementById('fileLabelText');
const processBtn = document.getElementById('processBtn');
const statusDiv = document.getElementById('status');
const previewContainer = document.getElementById('previewContainer');

let selectedFile = null;

fileInput.addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (!f) {
    selectedFile = null;
    fileLabelText.textContent = '📁 Choose Excel File (.xlsx)';
    processBtn.disabled = true;
    return;
  }
  selectedFile = f;
  fileLabelText.textContent = `✅ ${f.name}`;
  processBtn.disabled = false;
  statusDiv.textContent = '';
  previewContainer.innerHTML = '';
});

processBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  statusDiv.textContent = '⚙ Processing and downloading...';
  const fd = new FormData();
  fd.append('file', selectedFile);
  try {
    const res = await fetch('/', { method: 'POST', body: fd });
    if (!res.ok) {
      const text = await res.text();
      statusDiv.textContent = '❌ Processing failed: ' + text;
      return;
    }
    const blob = await res.blob();
    let filename = 'processed_revenue.xlsx';
    const cd = res.headers.get('Content-Disposition');
    if (cd) {
      const match = cd.match(/filename\*?=(?:UTF-8'')?\"?([^\";]+)/);
      if (match) filename = match[1];
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    statusDiv.textContent = '✅ Download complete!';
  } catch (err) {
    statusDiv.textContent = '⚠ Processing failed: ' + err.message;
  }
});
