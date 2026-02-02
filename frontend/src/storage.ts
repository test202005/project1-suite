// storage.ts - localStorage 封装
const AUTHOR_KEY = 'punch_agent_author';

export function getAuthor(): string | null {
  const author = localStorage.getItem(AUTHOR_KEY);
  return author;
}

export function setAuthor(author: string): void {
  localStorage.setItem(AUTHOR_KEY, author);
}

export function clearAuthor(): void {
  localStorage.removeItem(AUTHOR_KEY);
}
