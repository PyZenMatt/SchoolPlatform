const studentMenuItems = {
  items: [
    {
      id: 'dashboard',
      title: 'Dashboard',
      type: 'group',
      icon: 'icon-navigation',
      children: [
        {
          id: 'student-dashboard',
          title: 'Dashboard Studente',
          type: 'item',
          url: '/dashboard/student',
          icon: 'feather icon-home'
        }
      ]
    },
    {
      id: 'courses',
      title: 'Corsi',
      type: 'group',
      icon: 'icon-book',
      children: [
        {
          id: 'my-courses',
          title: 'I Miei Corsi',
          type: 'item',
          url: '/corsi',
          icon: 'feather icon-book-open'
        },
        {
          id: 'review-assigned',
          title: 'Peer Review',
          type: 'item',
          url: '/review/assigned',
          icon: 'feather icon-check-square'
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
        },
        {
          id: 'profile-progress',
          title: 'Progressi',
          type: 'item',
          url: '/profile/progress',
          icon: 'feather icon-trending-up'
        }
      ]
    }
  ]
};

export default studentMenuItems;
