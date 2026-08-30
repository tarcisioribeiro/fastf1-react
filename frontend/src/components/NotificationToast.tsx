import { useNotification, Notification } from '../contexts/NotificationContext';
import Icon, { type IconName } from './Icon';
import './NotificationToast.css';

export default function NotificationToast() {
  const { notifications, removeNotification } = useNotification();

  return (
    <div className="notification-container">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onClose: () => void;
}

function NotificationItem({ notification, onClose }: NotificationItemProps) {
  const { type, title, message } = notification;

  const icons: Record<string, IconName> = {
    success: 'check-circle',
    error: 'x-circle',
    warning: 'alert-circle',
    info: 'info',
  };

  return (
    <div className={`notification-toast ${type}`}>
      <div className="notification-icon">
        <Icon name={icons[type] ?? 'info'} size={20} />
      </div>
      <div className="notification-content">
        <div className="notification-title">{title}</div>
        <div className="notification-message">{message}</div>
      </div>
      <button className="notification-close" onClick={onClose} aria-label="Fechar">
        <Icon name="x" size={16} />
      </button>
    </div>
  );
}
