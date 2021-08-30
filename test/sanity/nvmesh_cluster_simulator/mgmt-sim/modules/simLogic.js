
exports.isUserAuthenticated = function(email, password) {
	console.log(`isUserAuthenticated called with username=${email} password=${password}`);
    var users = app.get('sim-data').users;
    var user = users.find(u => u.email == email);
    if (!user || user.password != password) {
        console.log(`isUserAuthenticated failed with username=${email} password=${password}`);
        return false
    } else
        return true
}