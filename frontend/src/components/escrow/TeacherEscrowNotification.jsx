import React, { useState, useEffect } from 'react';
import { Badge, Dropdown, ListGroup, Button } from 'react-bootstrap';
import { fetchUserNotifications, markNotificationRead } from '../../services/api/notifications';

/**
 * TeacherEscrowNotification Component
 * Shows escrow-related notifications in the navbar
 */
const TeacherEscrowNotification = ({ className = '' }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Load notifications
  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await fetchUserNotifications();
      
      // Filter escrow-related notifications
      const escrowNotifications = data.filter(notification => 
        notification.notification_type?.includes('escrow') ||
        notification.title?.toLowerCase().includes('escrow') ||
        notification.message?.toLowerCase().includes('escrow')
      );
      
      setNotifications(escrowNotifications);
      setUnreadCount(escrowNotifications.filter(n => !n.read).length);
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mark notification as read
  const handleMarkRead = async (notificationId) => {
    try {
      await markNotificationRead(notificationId);
      await loadNotifications(); // Refresh the list
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Load notifications on mount
  useEffect(() => {
    loadNotifications();
    
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Format notification time
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Ora';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m fa`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h fa`;
    return date.toLocaleDateString('it-IT');
  };

  return (
    <Dropdown className={className}>
      <Dropdown.Toggle variant="link" className="nav-link position-relative p-2">
        <i className="feather icon-shield" style={{ fontSize: '1.25rem' }}></i>
        {unreadCount > 0 && (
          <Badge 
            bg="warning" 
            className="position-absolute translate-middle badge rounded-pill"
            style={{ top: '8px', left: '20px', fontSize: '0.6em' }}
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
      </Dropdown.Toggle>

      <Dropdown.Menu align="end" style={{ width: '320px', maxHeight: '400px', overflowY: 'auto' }}>
        <div className="px-3 py-2 border-bottom">
          <h6 className="mb-0">
            <i className="feather icon-shield me-2"></i>
            Escrow TeoCoin
          </h6>
          <small className="text-muted">
            {unreadCount > 0 ? `${unreadCount} nuovi` : 'Tutto letto'}
          </small>
        </div>

        {loading ? (
          <div className="text-center py-3">
            <div className="spinner-border spinner-border-sm" role="status">
              <span className="visually-hidden">Caricamento...</span>
            </div>
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-4 text-muted">
            <i className="feather icon-check-circle mb-2" style={{ fontSize: '2rem' }}></i>
            <div>Nessuna notifica escrow</div>
          </div>
        ) : (
          <ListGroup variant="flush">
            {notifications.slice(0, 5).map(notification => (
              <ListGroup.Item 
                key={notification.id} 
                className={`border-0 ${!notification.read ? 'bg-light' : ''}`}
                style={{ cursor: 'pointer' }}
                onClick={() => !notification.read && handleMarkRead(notification.id)}
              >
                <div className="d-flex justify-content-between align-items-start">
                  <div className="flex-grow-1">
                    <div className="fw-semibold small mb-1">
                      {notification.title}
                    </div>
                    <div className="text-muted small mb-1">
                      {notification.message}
                    </div>
                    <div className="text-muted" style={{ fontSize: '0.7rem' }}>
                      {formatTime(notification.created_at)}
                    </div>
                  </div>
                  {!notification.read && (
                    <div className="ms-2">
                      <div 
                        className="bg-warning rounded-circle" 
                        style={{ width: '8px', height: '8px' }}
                      ></div>
                    </div>
                  )}
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}

        {notifications.length > 5 && (
          <div className="border-top p-2 text-center">
            <Button variant="link" size="sm" className="text-decoration-none">
              Vedi tutti gli escrow
            </Button>
          </div>
        )}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default TeacherEscrowNotification;
