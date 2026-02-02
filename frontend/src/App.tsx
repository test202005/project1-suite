import { useState, useEffect } from 'react';
import { submitInput, deleteFragment, type ApiResponse, type Fragment } from './api';
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
  const [clockedIn, setClockedIn] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [isAllView, setIsAllView] = useState(false);
  // 日期选择：每次刷新页面都回到今天，不持久化到 localStorage
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const todayStr = `${year}-${month}-${day}`;
    console.log('[App Init] Today date:', todayStr);
    return todayStr;
  });
  const [deleteConfirm, setDeleteConfirm] = useState<Fragment | null>(null);

  // 初始化：从 localStorage 读取 author 并查询今日碎片
  useEffect(() => {
    const savedAuthor = getAuthor();
    if (savedAuthor) {
      setAuthorState(savedAuthor);

      // 自动查询今日碎片
      submitInput({
        text: '今天做了啥',
        author: savedAuthor,
        date: selectedDate,
      }).then(response => {
        if (response.ok) {
          if (response.today_fragments.length > 0) {
            updateFragments(response.today_fragments);
          }
        }
      }).catch(err => {
        console.error('初始化查询失败:', err);
      });
    } else {
      setShowAuthorModal(true);
    }
  }, []);

  // 提取 summary（辅助函数）
  const extractSummary = (fragmentsList: Fragment[]): string | null => {
    // 查找最新的 type="summary" 的记录
    for (let i = fragmentsList.length - 1; i >= 0; i--) {
      if (fragmentsList[i].type === 'summary') {
        return fragmentsList[i].content;
      }
    }
    return null;
  };

  // 更新 fragments 并同步状态
  const updateFragments = (fragmentsList: Fragment[]) => {
    setFragments(fragmentsList);

    // 同步打卡状态
    const hasClockIn = fragmentsList.some(f =>
      f.content.includes('打卡') || f.content.includes('出勤')
    );
    if (hasClockIn !== clockedIn) {
      setClockedIn(hasClockIn);
    }

    // 同步 summary
    const summaryText = extractSummary(fragmentsList);
    if (summaryText) {
      setSummary(summaryText);
    }
  };

  // 日期变更处理
  const handleDateChange = async (newDate: string) => {
    setSelectedDate(newDate);

    // 查询该日期的数据
    try {
      const response = await submitInput({
        text: '今天做了啥',
        author: isAllView ? 'all' : author!,
        date: newDate,
      });

      if (response.ok) {
        updateFragments(response.today_fragments);
      }
    } catch (err) {
      console.error('切换日期失败:', err);
    }
  };

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
        date: selectedDate,
      });

      if (response.ok) {
        // 更新碎片列表和状态
        if (response.today_fragments.length > 0) {
          updateFragments(response.today_fragments);
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
          date: selectedDate,
        });
        if (response.ok) {
          updateFragments(response.today_fragments);
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

  // 打卡按钮
  const handleClockIn = async () => {
    if (!author) return;

    setLoading(true);
    setToast('');

    try {
      const response = await submitInput({
        text: '今天正常出勤，已完成打卡',
        author: author,
        date: selectedDate,
      });

      if (response.ok) {
        setClockedIn(true);
        setToast('打卡成功');
        setTimeout(() => setToast(''), 2000);

        // 更新碎片列表和状态
        if (response.today_fragments.length > 0) {
          updateFragments(response.today_fragments);
        }
      } else {
        setError(response.error || '打卡失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally {
      setLoading(false);
    }
  };

  // 删除碎片
  const handleDeleteFragment = async (fragment: Fragment) => {
    setLoading(true);
    setError('');

    try {
      const response = await deleteFragment(fragment.id);

      if (response.ok) {
        // 用返回的 today_fragments 更新列表
        if (response.today_fragments) {
          updateFragments(response.today_fragments);
        }
        setToast('删除成功');
        setTimeout(() => setToast(''), 2000);
      } else {
        setError(response.error || '删除失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '���络错误');
    } finally {
      setLoading(false);
      setDeleteConfirm(null);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>Punch Agent</h1>
        <div className="header-controls">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => handleDateChange(e.target.value)}
            className="date-picker"
            title="选择日期"
          />
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

      {/* Delete Confirm Modal */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>确认删除</h2>
            <p>确定要删除这条记录吗？</p>
            <p className="hint">{deleteConfirm.content.substring(0, 100)}...</p>
            <div className="modal-actions">
              <button onClick={() => setDeleteConfirm(null)}>取消</button>
              <button
                className="primary"
                onClick={() => handleDeleteFragment(deleteConfirm)}
              >
                删除
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

        {/* Summary Card */}
        {summary && (
          <section className="summary-card">
            <h3>📋 今日总结</h3>
            <pre className="summary-content">{summary}</pre>
          </section>
        )}

        {/* Quick Actions */}
        <section className="quick-actions">
          {!clockedIn && (
            <button
              onClick={handleClockIn}
              disabled={loading}
            >
              ⏰ 帮我打卡
            </button>
          )}
          <button
            onClick={() => quickSubmit('总结今日')}
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
                  <button
                    className="delete-btn"
                    onClick={() => setDeleteConfirm(fragment)}
                    title="删除"
                    disabled={loading}
                  >
                    🗑
                  </button>
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
