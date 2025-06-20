using Mutation360Team11.Enums;

namespace Mutation360Team11.Models;

public class Account
{
	public int Id { get; set; }
	public required string AccountName { get; set; }
	public string AccountDescription { get; set; } = null!;
	public AccountType AccountType { get; set; }
	public string AccountKey { get; set; }
}
