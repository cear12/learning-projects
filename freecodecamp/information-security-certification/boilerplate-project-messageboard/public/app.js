'use strict';

const pathParts = window.location.pathname.split('/').filter(Boolean);
const board = pathParts[0] === 'b' ? decodeURIComponent(pathParts[1] || '') : '';

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function formData(data) {
  return new URLSearchParams(data).toString();
}

async function send(url, method, data) {
  const response = await fetch(url, {
    method: method,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData(data || {})
  });
  const text = await response.text();
  if (!response.ok) throw new Error(text || 'Request failed');
  return text;
}

function addDeleteForm(parent, action, data, label) {
  const form = createElement('form', 'inline-form');
  const password = createElement('input');
  password.type = 'password';
  password.name = 'delete_password';
  password.placeholder = 'delete password';
  password.required = true;
  const button = createElement('button', 'danger', label);
  form.append(password, button);
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    try {
      const payload = Object.assign({}, data, { delete_password: password.value });
      const result = await send(action, 'DELETE', payload);
      window.alert(result);
      window.location.reload();
    } catch (error) {
      window.alert(error.message);
    }
  });
  parent.appendChild(form);
}

function addReportButton(parent, action, data, label) {
  const button = createElement('button', 'secondary', label || 'Report');
  button.type = 'button';
  button.addEventListener('click', async function () {
    try {
      const result = await send(action, 'PUT', data);
      window.alert(result);
    } catch (error) {
      window.alert(error.message);
    }
  });
  parent.appendChild(button);
}

function addReplyForm(parent, threadId) {
  const form = createElement('form', 'reply-form');
  const text = createElement('textarea');
  text.name = 'text';
  text.placeholder = 'Write a reply...';
  text.required = true;
  const password = createElement('input');
  password.type = 'password';
  password.name = 'delete_password';
  password.placeholder = 'delete password';
  password.required = true;
  const button = createElement('button', null, 'Reply');
  form.append(text, password, button);
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    try {
      const result = await send('/api/replies/' + encodeURIComponent(board), 'POST', {
        thread_id: threadId,
        text: text.value,
        delete_password: password.value
      });
      window.alert(result);
      window.location.reload();
    } catch (error) {
      window.alert(error.message);
    }
  });
  parent.appendChild(form);
}

function renderReply(parent, reply, threadId) {
  const article = createElement('article', 'reply');
  article.appendChild(createElement('p', 'meta', 'Reply ' + reply._id + ' · ' + new Date(reply.created_on).toLocaleString()));
  article.appendChild(createElement('p', null, reply.text));
  const actions = createElement('div', 'actions');
  addReportButton(actions, '/api/replies/' + encodeURIComponent(board), { thread_id: threadId, reply_id: reply._id });
  addDeleteForm(actions, '/api/replies/' + encodeURIComponent(board), { thread_id: threadId, reply_id: reply._id }, 'Delete reply');
  article.appendChild(actions);
  parent.appendChild(article);
}

function renderThread(parent, thread, includeLink) {
  const article = createElement('article', 'thread');
  article.appendChild(createElement('p', 'meta', 'Thread ' + thread._id + ' · ' + new Date(thread.created_on).toLocaleString()));
  article.appendChild(createElement('h2', null, thread.text));
  const actions = createElement('div', 'actions');
  addReportButton(actions, '/api/threads/' + encodeURIComponent(board), { thread_id: thread._id });
  addDeleteForm(actions, '/api/threads/' + encodeURIComponent(board), { thread_id: thread._id }, 'Delete thread');
  article.appendChild(actions);
  if (includeLink) {
    const link = createElement('a', 'thread-link', 'Open full thread (' + thread.replycount + ' replies)');
    link.href = '/b/' + encodeURIComponent(board) + '/' + encodeURIComponent(thread._id);
    article.appendChild(link);
  }
  const replies = createElement('div', 'replies');
  thread.replies.forEach(function (reply) { renderReply(replies, reply, thread._id); });
  article.appendChild(replies);
  addReplyForm(article, thread._id);
  parent.appendChild(article);
}

function addThreadForm(parent) {
  const form = createElement('form', 'thread-form');
  const text = createElement('textarea');
  text.name = 'text';
  text.placeholder = 'Start a new discussion...';
  text.required = true;
  const password = createElement('input');
  password.type = 'password';
  password.name = 'delete_password';
  password.placeholder = 'delete password';
  password.required = true;
  const button = createElement('button', null, 'Create thread');
  form.append(text, password, button);
  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    try {
      await send('/api/threads/' + encodeURIComponent(board), 'POST', {
        text: text.value,
        delete_password: password.value
      });
      window.location.reload();
    } catch (error) {
      window.alert(error.message);
    }
  });
  parent.appendChild(form);
}

async function loadBoard() {
  document.querySelector('#board-name').textContent = board;
  addThreadForm(document.querySelector('#new-thread'));
  const response = await fetch('/api/threads/' + encodeURIComponent(board));
  const threads = await response.json();
  const list = document.querySelector('#board-display');
  threads.forEach(function (thread) { renderThread(list, thread, true); });
}

async function loadSingleThread(threadId) {
  document.querySelector('#board-name').textContent = board + ' / thread';
  const response = await fetch('/api/replies/' + encodeURIComponent(board) + '?thread_id=' + encodeURIComponent(threadId));
  const thread = await response.json();
  if (!response.ok) throw new Error(thread.error || 'Thread not found');
  renderThread(document.querySelector('#board-display'), thread, false);
}

if (board) {
  (pathParts.length > 2 ? loadSingleThread(pathParts[2]) : loadBoard()).catch(function (error) {
    const target = document.querySelector('#board-display');
    if (target) target.appendChild(createElement('p', 'error', error.message));
  });
}
