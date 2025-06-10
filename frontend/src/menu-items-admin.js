const adminMenuItems = {
  items: [
    {
      id: 'dashboard',
      title: 'Dashboard',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'admin-dashboard',
          title: 'Dashboard Admin',
          type: 'item',
          url: '/dashboard/admin',
          icon: 'feather icon-home'
        }
      ]
    },
    {
      id: 'approvals',
      title: 'Approvazioni',
      type: 'group',
      icon: 'icon-check-circle',
      children: [
        {
          id: 'pending-courses',
          title: 'Corsi in Attesa',
          type: 'item',
          url: '/admin/pending-courses',
          icon: 'feather icon-clipboard',
          badge: {
            title: 'New',
            type: 'warning'
          }
        }
      ]
    },
    {
      id: 'courses',
      title: 'Gestione Corsi',
      type: 'group',
      icon: 'icon-book',
      children: [
        {
          id: 'all-courses',
          title: 'Tutti i Corsi',
          type: 'item',
          url: '/corsi',
          icon: 'feather icon-book-open'
        }
      ]
    },
    {
      id: 'wallet',
      title: 'Blockchain',
      type: 'group',
      icon: 'icon-wallet',
      children: [
        {
          id: 'wallet-connect',
          title: 'Wallet',
          type: 'item',
          url: '/test/rewards',
          icon: 'feather icon-credit-card'
        }
      ]
    },
    {
      id: 'profile',
      title: 'Profilo',
      type: 'group',
      icon: 'icon-user',
      children: [
        {
          id: 'my-profile',
          title: 'Il Mio Profilo',
          type: 'item',
          url: '/profile',
          icon: 'feather icon-user'
        },
        {
          id: 'notifications',
          title: 'Notifiche',
          type: 'item',
          url: '/profile/notifications',
          icon: 'feather icon-bell',
          badge: {
            title: 'New',
            type: 'primary'
          }
        },
        {
          id: 'profile-settings',
          title: 'Impostazioni',
          type: 'item',
          url: '/profile/settings',
          icon: 'feather icon-settings'
        }
      ]
    }
  ]
};

export default adminMenuItems;
