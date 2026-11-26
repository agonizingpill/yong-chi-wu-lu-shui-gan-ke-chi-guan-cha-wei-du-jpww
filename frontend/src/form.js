export function formData(form, numeric = []) {
  const data = Object.fromEntries(new FormData(form));
  for (const name of numeric) data[name] = Number(data[name]);
  return data;
}

export function handle(form, action) {
  if (!form) return;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const message = form.querySelector('[data-form-error]');
    const button = event.submitter || form.querySelector('button[type="submit"], button');
    try {
      if (message) message.textContent = '';
      if (button) button.disabled = true;
      await action(form);
    } catch (error) {
      if (message) message.textContent = error.message;
      else throw error;
    } finally {
      if (button) button.disabled = false;
    }
  });
}

export const inlineError = '<p data-form-error class="form-error" role="alert"></p>';
