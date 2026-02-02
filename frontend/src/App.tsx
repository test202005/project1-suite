import { useState, useEffect } from 'react';
import { submitInput, type ApiResponse, type Fragment } from './api';
import { getAuthor, setAuthor, clearAuthor } from './storage';
import './App.css';

function App() {
  // 状态管理
  const [author, setAuthorState] = useState<string | null>(null);
  const [showAuthorModal, setShowAuthorModal] = useState(false);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [fragments, setFragments] = useState<Fragment[]>([]);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');
  const [clockedIn, setClockedIn] = useState(false); // Mock 状态
  const [isAllView, setIsAllView] = useState(false);

  // 初始化：从 localStorage 读取 author 并查询今日碎片
  useEffect(() => {
    const savedAuthor = getAuthor();
    if (savedAuthor) {
      setAuthorState(savedAuthor);

      // 自动查询今日碎片
      submitInput({
        text: '今天做了啥',
        author: savedAuthor,
      }).then(response => {
        if (response.ok && response.today_fragments.length > 0) {
          setFragments(response.today_fragments);
        }
      }).catch(err => {
        console.error('初始化查询失败:', err);
      });
    } else {
      setShowAuthorModal(true);
    }
  }, []);

  // 提交输入
  const handleSubmit = async (inputText?: string) => {
    const textToSubmit = inputText || text;

    if (!textToSubmit.trim()) {
      setError('请输入内容');
      return;
    }

    if (!author) {
      setError('请先设置作者名称');
      setShowAuthorModal(true);
      return;
    }

    setLoading(true);
    setError('');
    setToast('');

    try {
      const response = await submitInput({
        text: textToSubmit,
        author: isAllView ? 'all' : author,
      });

      if (response.ok) {
        // 只在有新数据时更新列表
        if (response.today_fragments.length > 0) {
          setFragments(response.today_fragments);
        }

        // 未打卡提醒（不阻断）
        if (!clockedIn) {
          setToast('提醒：你今天还没打卡');
          setTimeout(() => setToast(''), 3000);
        }

        if (!inputText) {
          setText('');
        }
      } else {
        setError(response.error || '提交失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 保存 author
  const handleSaveAuthor = (newAuthor: string) => {
    const trimmed = newAuthor.trim();
    if (trimmed) {
      setAuthor(trimmed);
      setAuthorState(trimmed);
      setAuthor(trimmed);
      setShowAuthorModal(false);
      setError('');
    }
  };

  // 切换全组视图
  const toggleAllView = async () => {
    const newValue = !isAllView;
    setIsAllView(newValue);

    // 重新加载碎片
    if (fragments.length > 0) {
      try {
        const response = await submitInput({
          text: '今天做了啥',
          author: newValue ? 'all' : author!,
        });
        if (response.ok) {
          setFragments(response.today_fragments);
        }
      } catch (err) {
        console.error('切换视图失败:', err);
      }
    }
  };

  // 快捷操作
  const quickSubmit = (quickText: string) => {
    handleSubmit(quickText);
  };

  // 打卡按钮（本迭代只显示提示）
  const handleClockIn = () => {
    setToast('打卡功能将在后续迭代中支持');
    setTimeout(() => setToast(''), 3000);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>Punch Agent</h1>
        <div className="header-controls">
          <span className="clock-status">
            今日打卡：{clockedIn ? '已完成' : '未完成'}
          </span>
          <span className="author-display">
            当前: {isAllView ? '全组视图' : author || '未设置'}
          </span>
          <button
            className="icon-btn"
            onClick={() => setAuthorState(author)}
            title="修改作者"
          >
            ✏️
          </button>
          <button
            className={isAllView ? 'active' : ''}
            onClick={toggleAllView}
            title="切换全组视图"
          >
            👥 全组
          </button>
        </div>
      </header>

      {/* Author Modal */}
      {showAuthorModal && (
        <div className="modal-overlay" onClick={() => setShowAuthorModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>设置作者名称</h2>
            <input
              type="text"
              placeholder="请输入你的名字"
              defaultValue={author || ''}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSaveAuthor((e.target as HTMLInputElement).value);
                }
              }}
            />
            <div className="modal-actions">
              <button onClick={() => setShowAuthorModal(false)}>取消</button>
              <button
                className="primary"
                onClick={() => {
                  const input = document.querySelector('.modal input') as HTMLInputElement;
                  handleSaveAuthor(input?.value || '');
                }}
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="main">
        {/* Input Card */}
        <section className="input-card">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="记录今天的工作...（支持：完成、测试、修复、部署等事实性描述）"
            rows={4}
            disabled={loading}
          />
          {error && <div className="error">{error}</div>}
          <div className="input-actions">
            <button
              className="primary"
              onClick={() => handleSubmit()}
              disabled={loading || !text.trim()}
            >
              {loading ? '提交中...' : '提交'}
            </button>
          </div>
        </section>

        {/* Toast */}
        {toast && <div className="toast">{toast}</div>}

        {/* Quick Actions */}
        <section className="quick-actions">
          <button
            onClick={handleClockIn}
            disabled={loading}
          >
            ⏰ 帮我打卡
          </button>
          <button
            onClick={() => quickSubmit('今天做了啥')}
            disabled={loading}
          >
            📋 总结今日
          </button>
        </section>

        {/* Fragments List */}
        <section className="fragments-section">
          <h2>
            {isAllView ? '全组' : author || ''}今日碎片
            <span className="count">({fragments.length})</span>
          </h2>
          {fragments.length === 0 ? (
            <div className="empty-state">
              <p>今天还没有记录</p>
              <p className="hint">输入工作内容后点击"提交"按钮</p>
            </div>
          ) : (
            <ul className="fragments-list">
              {fragments.map((fragment, index) => (
                <li key={index} className="fragment-item">
                  {isAllView && fragment.author && (
                    <span className="fragment-author">{fragment.author}: </span>
                  )}
                  <span className="fragment-content">{fragment.content}</span>
                  <span className="fragment-time">
                    {new Date(fragment.created_at).toLocaleTimeString('zh-CN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
