if [ $1 -eq 0 ] ; then
    /sbin/service <%= update_init %> stop >/dev/null 2>&1
    /sbin/chkconfig --del <%= update_init %>
fi

