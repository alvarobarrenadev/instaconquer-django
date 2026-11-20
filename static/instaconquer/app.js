for (const form of document.querySelectorAll('[data-like-url]')) {
  const button = form.querySelector('button');
  const count = form.querySelector('.like-count');
  const status = form.querySelector('.like-status');
  let pending = false;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (pending) return;

    pending = true;
    button.setAttribute('aria-disabled', 'true');
    status.textContent = '';
    status.classList.add('visually-hidden');

    try {
      const response = await fetch(form.dataset.likeUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': form.elements.csrfmiddlewaretoken.value },
      });

      if (response.redirected) {
        window.location.reload();
        return;
      }
      if (!response.ok) throw new Error();

      const result = await response.json();
      button.setAttribute('aria-pressed', result.liked);
      count.textContent = result.nlikes;
      status.textContent = result.message;
    } catch {
      status.textContent = 'No se pudo actualizar el Me gusta. Inténtalo de nuevo.';
      status.classList.remove('visually-hidden');
    } finally {
      button.removeAttribute('aria-disabled');
      pending = false;
    }
  });
}

const photoForm = document.querySelector('[data-photo-form]');
if (photoForm) {
  const input = photoForm.elements.image;
  const preview = photoForm.querySelector('.photo-preview');
  let photoUrl;

  input.addEventListener('change', () => {
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    const file = input.files[0];

    if (file?.type.startsWith('image/')) {
      photoUrl = URL.createObjectURL(file);
      preview.src = photoUrl;
      preview.hidden = false;
    } else {
      photoUrl = undefined;
      preview.removeAttribute('src');
      preview.hidden = true;
    }
  });

  preview.addEventListener('error', () => { preview.hidden = true; });
}
